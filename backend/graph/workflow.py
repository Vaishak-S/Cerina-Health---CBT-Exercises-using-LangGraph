"""
LangGraph workflow definition for the Cerina Protocol Foundry.
Implements a Supervisor-Worker pattern with autonomous loops.
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from ..models.state import ProtocolState, AgentRole, create_initial_state
from ..agents.drafter import DrafterAgent
from ..agents.safety_guardian import SafetyGuardianAgent
from ..agents.clinical_critic import ClinicalCriticAgent
from ..agents.supervisor import SupervisorAgent


def should_continue(state: ProtocolState) -> Literal["continue", "human_approval", "end"]:
    """
    Routing function to determine next step in workflow.
    """
    # If human approval is required, route to human node
    if state.get("requires_human_approval") and not state.get("human_approved"):
        return "human_approval"
    
    # If human approved and we have human edits, process them
    if state.get("human_approved"):
        if state.get("human_edits"):
            # Route back to validation with human edits
            return "continue"
        else:
            # Workflow complete
            return "end"
    
    # If completed flag is set, end
    if state.get("completed"):
        return "end"
    
    # Check if we should continue iterating
    if state["iteration_count"] >= state["max_iterations"]:
        return "human_approval"
    
    # Continue workflow
    if state.get("next_agent"):
        return "continue"
    
    # Default to human approval if no clear next step
    return "human_approval"


def route_to_agent(state: ProtocolState) -> str:
    """
    Route to the appropriate agent based on state.
    """
    next_agent = state.get("next_agent")
    
    if next_agent == AgentRole.DRAFTER:
        return "drafter"
    elif next_agent == AgentRole.SAFETY_GUARDIAN:
        return "safety_guardian"
    elif next_agent == AgentRole.CLINICAL_CRITIC:
        return "clinical_critic"
    elif next_agent == AgentRole.SUPERVISOR:
        return "supervisor"
    else:
        # Default to supervisor if unclear
        return "supervisor"


async def process_human_feedback(state: ProtocolState) -> ProtocolState:
    """
    Process human feedback and edits.
    This node waits for human input via interrupt.
    """
    # If human has approved and provided edits, apply them
    if state.get("human_edits"):
        return {
            "current_draft": state["human_edits"],
            "final_protocol": state["human_edits"],
            "completed": True,
            "messages": [{
                "role": "assistant",
                "content": "Human feedback applied - workflow complete"
            }]
        }
    elif state.get("human_approved"):
        # No edits, just approval
        return {
            "final_protocol": state["current_draft"],
            "completed": True,
            "messages": [{
                "role": "assistant",
                "content": "Human approved - workflow complete"
            }]
        }
    
    # If we reach here without approval, this is the interrupt point
    # The workflow will pause here waiting for human input
    return state


def create_graph(checkpointer: BaseCheckpointSaver = None) -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Args:
        checkpointer: Checkpoint saver for persistence
    
    Returns:
        Compiled StateGraph
    """
    # Initialize agents
    drafter = DrafterAgent()
    safety_guardian = SafetyGuardianAgent()
    clinical_critic = ClinicalCriticAgent()
    supervisor = SupervisorAgent()
    
    # Create graph
    workflow = StateGraph(ProtocolState)
    
    # Add agent nodes
    workflow.add_node("drafter", drafter)
    workflow.add_node("safety_guardian", safety_guardian)
    workflow.add_node("clinical_critic", clinical_critic)
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("human_approval", process_human_feedback)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges from supervisor - determines routing
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: (
            "human_approval" if (state.get("requires_human_approval") and not state.get("human_approved"))
            else "end" if state.get("completed") or state.get("human_approved")
            else route_to_agent(state)
        ),
        {
            "drafter": "drafter",
            "safety_guardian": "safety_guardian",
            "clinical_critic": "clinical_critic",
            "supervisor": "supervisor",
            "human_approval": "human_approval",
            "end": END
        }
    )
    
    # All agents route back to supervisor
    workflow.add_edge("drafter", "supervisor")
    workflow.add_edge("safety_guardian", "supervisor")
    workflow.add_edge("clinical_critic", "supervisor")
    
    # Human approval can either end or continue
    workflow.add_conditional_edges(
        "human_approval",
        should_continue,
        {
            "continue": "supervisor",
            "human_approval": "human_approval",  # Stay in human approval if not approved
            "end": END
        }
    )
    
    # Compile graph with checkpointer
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer, interrupt_before=["human_approval"])
    else:
        return workflow.compile(interrupt_before=["human_approval"])


async def run_protocol_generation(
    user_intent: str,
    user_context: str = None,
    checkpointer: BaseCheckpointSaver = None,
    thread_id: str = "default"
):
    """
    Run the protocol generation workflow.
    
    Args:
        user_intent: The user's intent/request
        user_context: Optional additional context
        checkpointer: Checkpoint saver for persistence
        thread_id: Thread ID for checkpointing
    
    Returns:
        Final state after workflow completion
    """
    # Create graph
    graph = create_graph(checkpointer)
    
    # Create initial state
    initial_state = create_initial_state(user_intent, user_context)
    
    # Run graph
    config = {"configurable": {"thread_id": thread_id}}
    
    # Stream events
    final_state = None
    async for state in graph.astream(initial_state, config):
        final_state = state
        # You can emit events here for real-time updates
        
    return final_state
