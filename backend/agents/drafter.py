"""
Drafter Agent: Creates initial CBT exercise drafts and revises based on feedback.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..models.state import ProtocolState, AgentRole, ScratchpadEntry, DraftVersion
from datetime import datetime


class DrafterAgent:
    """Agent responsible for creating and revising CBT exercise drafts"""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.7):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.role = AgentRole.DRAFTER
        
    def create_system_prompt(self, state: ProtocolState) -> str:
        """Create system prompt based on current state"""
        base_prompt = """
        You are an expert CBT (Cognitive Behavioral Therapy) exercise designer.
        Your role is to create safe, empathetic, and clinically appropriate therapeutic exercises.
        Guidelines:
        - Use evidence-based CBT techniques
        - Ensure exercises are structured and actionable
        - Use empathetic, non-judgmental language
        - Include clear steps and guidance
        - Never provide medical diagnoses or prescriptions
        - Avoid content that could trigger self-harm
        """
        
        # Add revision context if this is a revision
        if state["needs_revision"] and state["revision_reason"]:
            revision_context = f"\n**REVISION REQUIRED**: {state['revision_reason']}\n"
            revision_context += "\nPrevious draft:\n" + state["current_draft"]
            
            # Add feedback from scratchpad
            recent_feedback = [
                entry for entry in state["scratchpad"]
                if entry.iteration == state["iteration_count"]
            ]
            if recent_feedback:
                revision_context += "\n\nAgent Feedback:\n"
                for entry in recent_feedback:
                    revision_context += f"- {entry.agent.value}: {entry.content}\n"
            
            base_prompt += revision_context
            
        return base_prompt
    
    def __call__(self, state: ProtocolState) -> Dict[str, Any]:
        """Execute the drafter agent"""
        print(f"[DRAFTER] Starting - iteration={state['iteration_count']}, needs_revision={state.get('needs_revision')}")
        iteration = state["iteration_count"]
        
        # Create prompt
        system_prompt = self.create_system_prompt(state)
        
        if state["needs_revision"]:
            user_message = f"""Based on the feedback above, revise the CBT exercise to address all concerns.
Maintain the therapeutic value while fixing the identified issues."""
        else:
            user_message = f"""Create a CBT exercise for the following intent:

User Intent: {state['user_intent']}

{f"Additional Context: {state['user_context']}" if state.get('user_context') else ""}

Create a complete, structured CBT exercise that addresses this intent."""
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        draft_content = response.content
        
        print(f"[DRAFTER] Generated draft: {len(draft_content)} characters")
        
        # Create draft version
        new_version = DraftVersion(
            version=len(state["draft_versions"]) + 1,
            content=draft_content,
            created_by=self.role
        )
        
        # Create scratchpad entry
        scratchpad_entry = ScratchpadEntry(
            agent=self.role,
            iteration=iteration,
            content=f"Created draft version {new_version.version}"
        )
        
        print(f"[DRAFTER] Completed - returning draft version {new_version.version}, routing to Safety Guardian")
        
        # Return updates to state
        return {
            "current_draft": draft_content,
            "draft_versions": [new_version],
            "scratchpad": [scratchpad_entry],
            "current_agent": self.role,
            "next_agent": AgentRole.SAFETY_GUARDIAN,
            "needs_revision": False,
            "revision_reason": None,
            "human_approved": None,  # Clear human approval flags after revision
            "human_feedback": None,  # Clear feedback after processing
            "messages": [{
                "role": "assistant",
                "content": f"Drafter: Created draft v{new_version.version}"
            }]
        }
