"""
State definitions for the Cerina Protocol Foundry.
This module defines the shared state ("blackboard") used by all agents.
"""
from typing import TypedDict, Annotated, List, Dict, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import operator


class AgentRole(str, Enum):
    """Agent roles in the system"""
    DRAFTER = "drafter"
    SAFETY_GUARDIAN = "safety_guardian"
    CLINICAL_CRITIC = "clinical_critic"
    SUPERVISOR = "supervisor"


class SafetyLevel(str, Enum):
    """Safety assessment levels"""
    SAFE = "safe"
    NEEDS_REVIEW = "needs_review"
    UNSAFE = "unsafe"


class ScratchpadEntry(BaseModel):
    """Individual entry in an agent's scratchpad"""
    agent: AgentRole
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str
    iteration: int


class DraftVersion(BaseModel):
    """A version of the CBT exercise draft"""
    version: int
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_by: AgentRole


class SafetyAssessment(BaseModel):
    """Safety evaluation results"""
    level: SafetyLevel
    concerns: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    flagged_lines: List[int] = Field(default_factory=list)


class ClinicalAssessment(BaseModel):
    """Clinical quality evaluation"""
    empathy_score: float = Field(ge=0.0, le=10.0)
    structure_score: float = Field(ge=0.0, le=10.0)
    clinical_appropriateness: float = Field(ge=0.0, le=10.0)
    feedback: str
    suggestions: List[str] = Field(default_factory=list)


class ProtocolState(TypedDict):
    """
    The main state object shared across all agents.
    This is the "blackboard" where agents collaborate.
    """
    # Input
    user_intent: str
    user_context: Optional[str]
    
    # Drafts and versions
    current_draft: str
    draft_versions: Annotated[List[DraftVersion], operator.add]
    
    # Scratchpad for agent collaboration
    scratchpad: Annotated[List[ScratchpadEntry], operator.add]
    
    # Assessments
    safety_assessment: Optional[SafetyAssessment]
    clinical_assessment: Optional[ClinicalAssessment]
    
    # Workflow metadata
    iteration_count: int
    max_iterations: int
    current_agent: Optional[AgentRole]
    next_agent: Optional[AgentRole]
    
    # Decision tracking
    needs_revision: bool
    revision_reason: Optional[str]
    
    # Human-in-the-loop
    requires_human_approval: bool
    human_approved: bool
    human_feedback: Optional[str]
    human_edits: Optional[str]
    
    # Final output
    final_protocol: Optional[str]
    completed: bool
    
    # Messages for conversational history
    messages: Annotated[List[Dict[str, str]], operator.add]


def create_initial_state(user_intent: str, user_context: Optional[str] = None) -> ProtocolState:
    """Create initial state for a new protocol generation request"""
    return ProtocolState(
        user_intent=user_intent,
        user_context=user_context,
        current_draft="",
        draft_versions=[],
        scratchpad=[],
        safety_assessment=None,
        clinical_assessment=None,
        iteration_count=0,
        max_iterations=5,
        current_agent=None,
        next_agent=AgentRole.SUPERVISOR,
        needs_revision=False,
        revision_reason=None,
        requires_human_approval=False,
        human_approved=False,
        human_feedback=None,
        human_edits=None,
        final_protocol=None,
        completed=False,
        messages=[]
    )
