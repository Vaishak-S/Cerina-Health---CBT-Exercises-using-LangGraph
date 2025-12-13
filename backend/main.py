"""
FastAPI application for the Cerina Protocol Foundry.
Provides REST API and WebSocket endpoints for the multi-agent system.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

from .database.checkpointer import get_checkpointer, init_database
from .database.history import init_history_db, ProtocolHistory, SessionLocal
from .graph.workflow import create_graph, create_initial_state
from .models.state import ProtocolState

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Cerina Protocol Foundry API",
    description="Multi-agent system for CBT exercise generation",
    version="1.0.0"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and checkpointer
checkpointer = init_database()
init_history_db()

# Global graph instance
graph = create_graph(checkpointer)


# Request/Response Models
class ProtocolRequest(BaseModel):
    user_intent: str
    user_context: Optional[str] = None


class ProtocolResponse(BaseModel):
    protocol_id: str
    status: str
    message: str


class HumanFeedback(BaseModel):
    approved: bool
    feedback: Optional[str] = None
    edits: Optional[str] = None


class StateResponse(BaseModel):
    protocol_id: str
    current_draft: str
    draft_versions: List[dict]
    iteration_count: int
    safety_assessment: Optional[dict] = None
    clinical_assessment: Optional[dict] = None
    scratchpad: List[dict]
    requires_human_approval: bool
    completed: bool


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, protocol_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[protocol_id] = websocket
    
    def disconnect(self, protocol_id: str):
        if protocol_id in self.active_connections:
            del self.active_connections[protocol_id]
    
    async def send_update(self, protocol_id: str, data: dict):
        if protocol_id in self.active_connections:
            try:
                await self.active_connections[protocol_id].send_json(data)
            except:
                self.disconnect(protocol_id)


manager = ConnectionManager()


# API Endpoints
@app.get("/api/protocols/latest")
async def get_latest_protocol():
    """
    Get the most recently created incomplete protocol ID.
    Only returns if it's the absolute latest protocol (indicating potential server failure).
    Returns 404 if no incomplete protocols exist or if completed protocols are newer.
    """
    try:
        db = SessionLocal()
        
        # Get the absolute latest protocol (completed or not)
        absolute_latest = db.query(ProtocolHistory).order_by(
            ProtocolHistory.created_at.desc()
        ).first()
        
        if not absolute_latest:
            db.close()
            raise HTTPException(status_code=404, detail="No protocols found")
        
        # Only return if the latest protocol is incomplete (suggests server failure)
        if absolute_latest.completed_at is None:
            db.close()
            return {"protocol_id": absolute_latest.id}
        
        # If latest protocol is complete, no need to auto-resume
        db.close()
        raise HTTPException(status_code=404, detail="No incomplete protocols to resume")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/protocols", response_model=ProtocolResponse)
async def create_protocol(request: ProtocolRequest):
    """
    Create a new protocol generation request.
    This starts the multi-agent workflow.
    """
    protocol_id = str(uuid.uuid4())
    
    try:
        # Create initial state
        initial_state = create_initial_state(request.user_intent, request.user_context)
        
        # Save to history
        db = SessionLocal()
        history = ProtocolHistory(
            id=protocol_id,
            user_intent=request.user_intent,
            user_context=request.user_context
        )
        db.add(history)
        db.commit()
        db.close()
        
        # Start workflow in background
        config = {"configurable": {"thread_id": protocol_id}}
        
        # Run workflow asynchronously - it will execute until interrupt
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_workflow_sync, protocol_id, initial_state, config)
        
        # Don't wait for result - let it run in background
        def log_completion(fut):
            try:
                result = fut.result()
                if result:
                    print(f"[WORKFLOW] Protocol {protocol_id} completed:")
                    print(f"  - requires_approval={result.get('requires_human_approval')}")
                    print(f"  - completed={result.get('completed')}")
                else:
                    print(f"[WORKFLOW] Protocol {protocol_id}: No result returned")
            except Exception as e:
                print(f"[WORKFLOW ERROR] Protocol {protocol_id}: {e}")
                import traceback
                traceback.print_exc()
        
        future.add_done_callback(log_completion)
        
        return ProtocolResponse(
            protocol_id=protocol_id,
            status="processing",
            message="Protocol generation started"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_workflow_sync(protocol_id: str, initial_state: ProtocolState, config: dict):
    """Run workflow synchronously until it hits interrupt or completes"""
    try:
        print(f"[WORKFLOW] Starting workflow for protocol {protocol_id}")
        print(f"[WORKFLOW] Config: {config}")
        print(f"[WORKFLOW] Initial state keys: {list(initial_state.keys())}")
        
        # Invoke will run until interrupt_before is hit or workflow completes
        # LangGraph handles mixed sync/async nodes automatically
        result = graph.invoke(initial_state, config)
        
        print(f"[WORKFLOW] Invoke returned: {type(result)}")
        if result:
            print(f"[WORKFLOW] Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
        
        # After invoke, get the current state from the result itself
        # The invoke() method returns the final state dict directly
        if result and isinstance(result, dict):
            print(f"[WORKFLOW] Workflow stopped at checkpoint:")
            print(f"  - iteration_count={result.get('iteration_count')}")
            print(f"  - requires_approval={result.get('requires_human_approval')}")
            print(f"  - completed={result.get('completed')}")
            print(f"  - current_draft exists={bool(result.get('current_draft'))}")
            print(f"  - current_agent={result.get('current_agent')}")
            return result
        else:
            print(f"[WORKFLOW] No checkpoint found for protocol {protocol_id}")
            return None
    except Exception as e:
        print(f"[WORKFLOW ERROR] Protocol {protocol_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


@app.get("/api/protocols/{protocol_id}/state", response_model=StateResponse)
async def get_protocol_state(protocol_id: str):
    """
    Get current state of a protocol generation workflow.
    """
    try:
        config = {"configurable": {"thread_id": protocol_id}}
        state = graph.get_state(config)
        
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        values = state.values
        
        # Convert safety assessment to dict
        safety_dict = None
        if values.get("safety_assessment"):
            sa = values["safety_assessment"]
            safety_dict = {
                "level": sa.level.value,
                "concerns": sa.concerns,
                "recommendations": sa.recommendations,
                "flagged_lines": sa.flagged_lines
            }
        
        # Convert clinical assessment to dict
        clinical_dict = None
        if values.get("clinical_assessment"):
            ca = values["clinical_assessment"]
            clinical_dict = {
                "empathy_score": ca.empathy_score,
                "structure_score": ca.structure_score,
                "clinical_appropriateness": ca.clinical_appropriateness,
                "feedback": ca.feedback,
                "suggestions": ca.suggestions
            }
        
        # Convert draft versions to dict
        draft_versions_list = []
        for version in values.get("draft_versions", []):
            draft_versions_list.append({
                "version": version.version,
                "content": version.content,
                "timestamp": version.timestamp.isoformat(),
                "created_by": version.created_by.value
            })
        
        return StateResponse(
            protocol_id=protocol_id,
            current_draft=values.get("current_draft", ""),
            draft_versions=draft_versions_list,
            iteration_count=values.get("iteration_count", 0),
            safety_assessment=safety_dict,
            clinical_assessment=clinical_dict,
            scratchpad=[
                {
                    "agent": entry.agent.value,
                    "content": entry.content,
                    "iteration": entry.iteration,
                    "timestamp": entry.timestamp.isoformat()
                }
                for entry in values.get("scratchpad", [])
            ],
            requires_human_approval=values.get("requires_human_approval", False),
            completed=values.get("completed", False)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"Error in get_protocol_state: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/protocols/{protocol_id}/feedback")
async def submit_human_feedback(protocol_id: str, feedback: HumanFeedback):
    """
    Submit human feedback to resume workflow.
    """
    try:
        config = {"configurable": {"thread_id": protocol_id}}
        
        # Get current state (use sync method)
        state = graph.get_state(config)
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        print(f"[FEEDBACK] Received for protocol {protocol_id}: approved={feedback.approved}")
        
        # Update the state with human feedback FIRST using update_state
        update = {
            "requires_human_approval": False  # Clear the flag to allow workflow to continue
        }
        
        # If approved, mark as completed
        if feedback.approved:
            update["human_approved"] = True
            update["completed"] = True
            # If user provided edits, apply them immediately to current_draft
            if feedback.edits:
                update["current_draft"] = feedback.edits
                update["final_protocol"] = feedback.edits
                print(f"[FEEDBACK] Applying edits immediately to current_draft")
            else:
                # No edits - use existing draft as final
                update["final_protocol"] = state.values.get("current_draft")
            print(f"[FEEDBACK] Workflow approved - marking as completed")
        else:
            # Request revision - send back to agents
            update["human_approved"] = False
            update["human_feedback"] = feedback.feedback or "Human requested revisions"
            update["needs_revision"] = True
            update["revision_reason"] = feedback.feedback or "Human requested revisions"
            update["next_agent"] = "drafter"  # Route back to drafter
            update["completed"] = False  # Ensure workflow is not marked complete
            # Clear assessments so they're re-evaluated
            update["safety_assessment"] = None
            update["clinical_assessment"] = None
            # If user edited before requesting revision, use the edited version
            if feedback.edits:
                update["current_draft"] = feedback.edits
                update["human_edits"] = feedback.edits
                
                # Add edited version to history
                from backend.models.state import DraftVersion, AgentRole
                from datetime import datetime
                
                current_versions = state.values.get("draft_versions", [])
                new_version = DraftVersion(
                    version=len(current_versions) + 1,
                    content=feedback.edits,
                    timestamp=datetime.utcnow(),
                    created_by=AgentRole.HUMAN
                )
                update["draft_versions"] = [new_version]
                
                print(f"[FEEDBACK] Revision requested with edits - updating current_draft and creating version {new_version.version}")
            else:
                print(f"[FEEDBACK] Revision requested without edits")
        
        # Update state before resuming
        graph.update_state(config, update)
        print(f"[FEEDBACK] State updated")
        
        # Resume workflow in background to run final nodes
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        def resume_workflow():
            print(f"[FEEDBACK] Resuming workflow for {protocol_id}")
            try:
                # Resume from interrupt by invoking with None
                result = graph.invoke(None, config)
                print(f"[FEEDBACK] Workflow step completed for {protocol_id}")
                print(f"[FEEDBACK] Final state: completed={result.get('completed')}, requires_approval={result.get('requires_human_approval')}")
                return result
            except Exception as e:
                print(f"[FEEDBACK ERROR] {protocol_id}: {e}")
                import traceback
                traceback.print_exc()
        
        future = executor.submit(resume_workflow)
        
        # Don't wait - let it complete in background
        def log_completion(fut):
            try:
                result = fut.result()
                print(f"[FEEDBACK] Protocol {protocol_id} finalized")
            except Exception as e:
                print(f"[FEEDBACK ERROR] Protocol {protocol_id}: {e}")
        
        future.add_done_callback(log_completion)
        
        # Update history immediately
        db = SessionLocal()
        history = db.query(ProtocolHistory).filter_by(id=protocol_id).first()
        if history:
            history.human_approved = feedback.approved
            history.human_feedback = feedback.feedback
            
            if feedback.approved:
                # On approval, set final protocol and completion time
                if feedback.edits:
                    history.final_protocol = feedback.edits
                else:
                    history.final_protocol = state.values.get("current_draft")
                history.completed_at = datetime.utcnow()
                print(f"[FEEDBACK] Database updated: final_protocol saved, completed_at set")
            else:
                # On revision, update final_protocol with edits but don't set completed_at
                if feedback.edits:
                    history.final_protocol = feedback.edits
                    print(f"[FEEDBACK] Database updated: final_protocol updated with edits")
            
            db.commit()
        db.close()
        
        return {"status": "success", "message": "Feedback submitted and workflow resumed"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/protocols/{protocol_id}/save")
async def save_draft(protocol_id: str, request: dict):
    """
    Save the current draft to the database and update the graph state with a new version.
    """
    try:
        draft_content = request.get("draft")
        if not draft_content:
            raise HTTPException(status_code=400, detail="Draft content is required")
        
        config = {"configurable": {"thread_id": protocol_id}}
        
        # Get current state
        state = graph.get_state(config)
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="Protocol not found in graph")
        
        # Create new draft version
        from backend.models.state import DraftVersion, AgentRole
        from datetime import datetime
        
        current_versions = state.values.get("draft_versions", [])
        new_version_number = len(current_versions) + 1
        
        new_version = DraftVersion(
            version=new_version_number,
            content=draft_content,
            timestamp=datetime.utcnow(),
            created_by=AgentRole.HUMAN  # Mark as human-edited
        )
        
        # Update the graph state - use operator.add by passing a list with the new version
        update = {
            "current_draft": draft_content,
            "draft_versions": [new_version]  # operator.add will append this
        }
        
        graph.update_state(config, update)
        print(f"[SAVE] Draft saved and new version created: v{new_version_number}")
        
        # Also update database history
        db = SessionLocal()
        history = db.query(ProtocolHistory).filter_by(id=protocol_id).first()
        if history:
            history.final_protocol = draft_content
            db.commit()
        db.close()
        
        return {"status": "success", "message": "Draft saved successfully", "version": new_version_number}
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{protocol_id}")
async def websocket_endpoint(websocket: WebSocket, protocol_id: str):
    """
    WebSocket endpoint for real-time updates.
    """
    await manager.connect(protocol_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(protocol_id)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Cerina Protocol Foundry"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
