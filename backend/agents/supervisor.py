"""
Supervisor Agent: Orchestrates workflow, routes tasks, and decides when draft is complete.
"""
from typing import Dict, Any
from ..models.state import ProtocolState, AgentRole, ScratchpadEntry, SafetyLevel


class SupervisorAgent:
    """Agent responsible for workflow orchestration and decision-making"""
    
    def __init__(self):
        self.role = AgentRole.SUPERVISOR
        
    def __call__(self, state: ProtocolState) -> Dict[str, Any]:
        """Execute the supervisor agent"""
        iteration = state["iteration_count"]
        max_iterations = state["max_iterations"]
        
        # Increment iteration
        new_iteration = iteration + 1
        
        # Decision logic
        decision_log = []
        
        # Check if we've exceeded max iterations
        if new_iteration >= max_iterations:
            decision_log.append(f"Max iterations ({max_iterations}) reached")
            return self._complete_workflow(state, decision_log, "max_iterations_reached")
        
        # Check safety - must be safe to proceed
        if state.get("safety_assessment"):
            safety_level = state["safety_assessment"].level
            if safety_level == SafetyLevel.UNSAFE:
                decision_log.append("UNSAFE draft detected - requesting revision")
                return self._request_revision(state, new_iteration, decision_log)
            elif safety_level == SafetyLevel.NEEDS_REVIEW:
                decision_log.append("Safety concerns identified - requesting revision")
                return self._request_revision(state, new_iteration, decision_log)
        
        # Check clinical quality
        if state.get("clinical_assessment"):
            clinical = state["clinical_assessment"]
            avg_score = (
                clinical.empathy_score +
                clinical.structure_score +
                clinical.clinical_appropriateness
            ) / 3.0
            
            if avg_score < 7.0:
                decision_log.append(f"Clinical quality below threshold ({avg_score:.1f}/10) - requesting revision")
                return self._request_revision(state, new_iteration, decision_log)
            else:
                decision_log.append(f"Clinical quality acceptable ({avg_score:.1f}/10)")
        
        # If we already have assessments and they're good, move to human approval
        if state.get("safety_assessment") and state.get("clinical_assessment"):
            if not state.get("needs_revision"):
                decision_log.append("All checks passed - ready for human approval")
                return self._request_human_approval(state, new_iteration, decision_log)
        
        # If we need revision, route to drafter
        if state.get("needs_revision"):
            decision_log.append("Revision required - routing to Drafter")
            return self._request_revision(state, new_iteration, decision_log)
        
        # Default: continue workflow (should not normally reach here)
        decision_log.append("Continuing workflow")
        return {
            "iteration_count": new_iteration,
            "current_agent": self.role,
            "next_agent": AgentRole.DRAFTER,
            "scratchpad": [ScratchpadEntry(
                agent=self.role,
                iteration=new_iteration,
                content="Supervisor: " + "; ".join(decision_log)
            )],
            "messages": [{
                "role": "assistant",
                "content": f"Supervisor (iter {new_iteration}): Continuing workflow"
            }]
        }
    
    def _request_revision(self, state: ProtocolState, new_iteration: int, decision_log: list) -> Dict[str, Any]:
        """Request a revision from the drafter"""
        return {
            "iteration_count": new_iteration,
            "current_agent": self.role,
            "next_agent": AgentRole.DRAFTER,
            "needs_revision": True,
            "scratchpad": [ScratchpadEntry(
                agent=self.role,
                iteration=new_iteration,
                content="Supervisor: " + "; ".join(decision_log)
            )],
            "messages": [{
                "role": "assistant",
                "content": f"Supervisor (iter {new_iteration}): Requesting revision"
            }]
        }
    
    def _request_human_approval(self, state: ProtocolState, new_iteration: int, decision_log: list) -> Dict[str, Any]:
        """Mark that human approval is required"""
        return {
            "iteration_count": new_iteration,
            "current_agent": self.role,
            "next_agent": None,
            "requires_human_approval": True,
            "scratchpad": [ScratchpadEntry(
                agent=self.role,
                iteration=new_iteration,
                content="Supervisor: " + "; ".join(decision_log) + " - AWAITING HUMAN APPROVAL"
            )],
            "messages": [{
                "role": "assistant",
                "content": f"Supervisor (iter {new_iteration}): Ready for human approval"
            }]
        }
    
    def _complete_workflow(self, state: ProtocolState, decision_log: list, reason: str) -> Dict[str, Any]:
        """Complete the workflow"""
        return {
            "iteration_count": state["iteration_count"] + 1,
            "current_agent": self.role,
            "next_agent": None,
            "requires_human_approval": True,
            "scratchpad": [ScratchpadEntry(
                agent=self.role,
                iteration=state["iteration_count"] + 1,
                content=f"Supervisor: Workflow complete - {reason}"
            )],
            "messages": [{
                "role": "assistant",
                "content": f"Supervisor: Workflow complete - {reason}"
            }]
        }
