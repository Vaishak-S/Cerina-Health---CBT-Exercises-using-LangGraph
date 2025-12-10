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
        
        # Run until interrupt (human approval) in background thread
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor()
        executor.submit(run_workflow_until_interrupt_sync, protocol_id, initial_state, config)
        
        return ProtocolResponse(
            protocol_id=protocol_id,
            status="processing",
            message="Protocol generation started"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_workflow_until_interrupt_sync(protocol_id: str, initial_state: ProtocolState, config: dict):
    """Run workflow in background until it hits human approval interrupt"""
    try:
        for event in graph.stream(initial_state, config):
            # Send real-time updates via WebSocket (sync - manager handles async)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(manager.send_update(protocol_id, {
                "type": "state_update",
                "data": event
            }))
            
            # Check if we hit human approval interrupt
            if event.get("requires_human_approval"):
                loop.run_until_complete(manager.send_update(protocol_id, {
                    "type": "human_approval_required",
                    "protocol_id": protocol_id
                }))
                break
    except Exception as e:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(manager.send_update(protocol_id, {
            "type": "error",
            "message": str(e)
        }))


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
        
        return StateResponse(
            protocol_id=protocol_id,
            current_draft=values.get("current_draft", ""),
            iteration_count=values.get("iteration_count", 0),
            safety_assessment=values.get("safety_assessment"),
            clinical_assessment=values.get("clinical_assessment"),
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
        
        # Get current state
        state = await graph.aget_state(config)
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        # Update state with human feedback
        update = {
            "human_approved": feedback.approved,
            "human_feedback": feedback.feedback,
            "human_edits": feedback.edits
        }
        
        # Resume workflow
        for event in graph.stream(update, config):
            await manager.send_update(protocol_id, {
                "type": "state_update",
                "data": event
            })
        
        # Update history
        db = SessionLocal()
        history = db.query(ProtocolHistory).filter_by(id=protocol_id).first()
        if history:
            history.human_approved = feedback.approved
            history.human_feedback = feedback.feedback
            if feedback.edits:
                history.final_protocol = feedback.edits
            history.completed_at = datetime.utcnow()
            db.commit()
        db.close()
        
        return {"status": "success", "message": "Feedback submitted and workflow resumed"}
    
    except HTTPException:
        raise
    except Exception as e:
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
