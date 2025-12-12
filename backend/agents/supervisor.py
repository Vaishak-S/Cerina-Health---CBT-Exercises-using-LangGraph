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
        print(f"[SUPERVISOR] Starting - iteration={state['iteration_count']}")
        iteration = state["iteration_count"]
        max_iterations = state["max_iterations"]
        
        # Increment iteration
        new_iteration = iteration + 1
        
        # Log current state
        safety_level = state.get('safety_assessment').level.value if state.get('safety_assessment') else 'none'
        clinical_assess = state.get('clinical_assessment')
        clinical_avg = 'none'
        if clinical_assess:
            clinical_avg = f"{((clinical_assess.empathy_score + clinical_assess.structure_score + clinical_assess.clinical_appropriateness) / 3.0):.1f}"
        print(f"[SUPERVISOR] State: has_draft={bool(state.get('current_draft'))}, safety={safety_level}, clinical_avg={clinical_avg}")
        print(f"[SUPERVISOR] human_approved={state.get('human_approved')}, needs_revision={state.get('needs_revision')}, has_safety={bool(state.get('safety_assessment'))}, has_clinical={bool(state.get('clinical_assessment'))}")
        
        # Decision logic
        decision_log = []
        
        # FIRST: Check if revision is needed (explicit flag set by feedback endpoint)
        if state.get("needs_revision") == True:
            decision_log.append(f"Revision needed: {state.get('revision_reason') or state.get('human_feedback') or 'Quality issues detected'}")
            print(f"[SUPERVISOR] Decision: REVISION NEEDED - route to DRAFTER")
            # Clear assessments so they get re-evaluated, and clear the revision flag
            result = self._request_revision(state, new_iteration, decision_log, clear_assessments=True)
            # IMPORTANT: After routing to drafter, don't keep the human_approved=False flag
            result["human_approved"] = None  # Clear it so we don't loop
            return result
        
        # Check if we've exceeded max iterations
        if new_iteration >= max_iterations:
            decision_log.append(f"Max iterations ({max_iterations}) reached")
            return self._complete_workflow(state, decision_log, "max_iterations_reached")
        
        # If no draft exists yet, route to drafter
        if not state.get("current_draft"):
            decision_log.append("No draft yet - routing to Drafter")
            print(f"[SUPERVISOR] Decision: Route to DRAFTER (no draft yet)")
            return self._route_to_agent(state, new_iteration, decision_log, AgentRole.DRAFTER, needs_revision=False)
        
        # If we have a draft but no safety assessment, route to safety guardian
        if state.get("current_draft") and not state.get("safety_assessment"):
            decision_log.append("Draft exists, needs safety check")
            print(f"[SUPERVISOR] Decision: Route to SAFETY_GUARDIAN")
            return self._route_to_agent(state, new_iteration, decision_log, AgentRole.SAFETY_GUARDIAN)
        
        # Check safety - must be safe to proceed
        if state.get("safety_assessment"):
            safety_level = state["safety_assessment"].level
            if safety_level == SafetyLevel.UNSAFE:
                decision_log.append("UNSAFE draft detected - requesting revision")
                print(f"[SUPERVISOR] Decision: UNSAFE - route to DRAFTER for revision")
                return self._request_revision(state, new_iteration, decision_log)
            elif safety_level == SafetyLevel.NEEDS_REVIEW:
                decision_log.append("Safety concerns identified - requesting revision")
                print(f"[SUPERVISOR] Decision: Safety NEEDS_REVIEW - route to DRAFTER for revision")
                return self._request_revision(state, new_iteration, decision_log)
        
        # If safety is OK but no clinical assessment, route to clinical critic
        if state.get("safety_assessment") and not state.get("clinical_assessment"):
            decision_log.append("Safety check passed, needs clinical evaluation")
            print(f"[SUPERVISOR] Decision: Route to CLINICAL_CRITIC")
            return self._route_to_agent(state, new_iteration, decision_log, AgentRole.CLINICAL_CRITIC)
        
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
                print(f"[SUPERVISOR] Decision: Clinical score low - route to DRAFTER for revision")
                return self._request_revision(state, new_iteration, decision_log)
            else:
                decision_log.append(f"Clinical quality acceptable ({avg_score:.1f}/10)")
        
        # If we already have assessments and they're good, move to human approval
        if state.get("safety_assessment") and state.get("clinical_assessment"):
            if not state.get("needs_revision"):
                decision_log.append("All checks passed - ready for human approval")
                print(f"[SUPERVISOR] Decision: Request HUMAN_APPROVAL")
                return self._request_human_approval(state, new_iteration, decision_log)
        
        # If we need revision, route to drafter
        if state.get("needs_revision"):
            decision_log.append("Revision required - routing to Drafter")
            print(f"[SUPERVISOR] Decision: Route to DRAFTER (revision needed)")
            return self._request_revision(state, new_iteration, decision_log)
        
        # Default fallback (should not reach here)
        decision_log.append("No clear decision - defaulting to Drafter")
        print(f"[SUPERVISOR] Decision: FALLBACK - route to DRAFTER")
        return self._route_to_agent(state, new_iteration, decision_log, AgentRole.DRAFTER)
    
    def _request_revision(self, state: ProtocolState, new_iteration: int, decision_log: list, clear_assessments: bool = False) -> Dict[str, Any]:
        """Request a revision from the drafter"""
        result = {
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
        
        # If human requested revision, clear assessments so they're re-evaluated
        if clear_assessments:
            result["safety_assessment"] = None
            result["clinical_assessment"] = None
            print("[SUPERVISOR] Cleared assessments for re-evaluation after human revision")
        
        return result
    
    def _route_to_agent(self, state: ProtocolState, new_iteration: int, decision_log: list, next_agent: AgentRole, needs_revision: bool = False) -> Dict[str, Any]:
        """Route to a specific agent"""
        return {
            "iteration_count": new_iteration,
            "current_agent": self.role,
            "next_agent": next_agent,
            "needs_revision": needs_revision,
            "scratchpad": [ScratchpadEntry(
                agent=self.role,
                iteration=new_iteration,
                content="Supervisor: " + "; ".join(decision_log)
            )],
            "messages": [{
                "role": "assistant",
                "content": f"Supervisor (iter {new_iteration}): Routing to {next_agent.value}"
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
