"""
Clinical Critic Agent: Evaluates clinical quality, empathy, and structure of CBT exercises.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from ..models.state import ProtocolState, AgentRole, ScratchpadEntry, ClinicalAssessment
import json


class ClinicalCriticAgent:
    """Agent responsible for clinical quality evaluation"""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.3):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.role = AgentRole.CLINICAL_CRITIC
        self.parser = JsonOutputParser()
        
    def create_system_prompt(self) -> str:
        """Create system prompt for clinical evaluation"""
        return """You are a Clinical Critic specializing in CBT therapeutic exercises.
Your role is to evaluate the clinical quality, empathy, and structure of exercises.

Evaluate:
1. **Empathy** (0-10): Warmth, validation, non-judgmental tone
2. **Structure** (0-10): Clear steps, logical flow, actionable guidance
3. **Clinical Appropriateness** (0-10): Evidence-based techniques, therapeutic value

Provide constructive feedback and specific suggestions for improvement.

Respond with a JSON object:
{
    "empathy_score": 8.5,
    "structure_score": 7.0,
    "clinical_appropriateness": 9.0,
    "feedback": "detailed evaluation",
    "suggestions": ["specific improvements"]
}
"""
    
    async def __call__(self, state: ProtocolState) -> Dict[str, Any]:
        """Execute the clinical critic agent"""
        iteration = state["iteration_count"]
        current_draft = state["current_draft"]
        
        # Create evaluation prompt
        system_prompt = self.create_system_prompt()
        user_message = f"""Evaluate this CBT exercise draft:

User Intent: {state['user_intent']}

Draft:
{current_draft}

Provide your clinical assessment as JSON."""
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse JSON response
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            assessment_data = json.loads(content)
        except:
            # Fallback if parsing fails
            assessment_data = {
                "empathy_score": 5.0,
                "structure_score": 5.0,
                "clinical_appropriateness": 5.0,
                "feedback": "Unable to parse assessment",
                "suggestions": ["Manual review required"]
            }
        
        # Create clinical assessment
        clinical_assessment = ClinicalAssessment(
            empathy_score=float(assessment_data.get("empathy_score", 5.0)),
            structure_score=float(assessment_data.get("structure_score", 5.0)),
            clinical_appropriateness=float(assessment_data.get("clinical_appropriateness", 5.0)),
            feedback=assessment_data.get("feedback", ""),
            suggestions=assessment_data.get("suggestions", [])
        )
        
        # Calculate average score
        avg_score = (
            clinical_assessment.empathy_score +
            clinical_assessment.structure_score +
            clinical_assessment.clinical_appropriateness
        ) / 3.0
        
        # Determine if revision is needed (threshold: 7.0)
        needs_revision = avg_score < 7.0
        revision_reason = None
        if needs_revision:
            revision_reason = f"Clinical quality below threshold (avg: {avg_score:.1f}/10). {clinical_assessment.feedback}"
        
        # Create scratchpad entry
        scratchpad_content = f"Scores - Empathy: {clinical_assessment.empathy_score:.1f}, "
        scratchpad_content += f"Structure: {clinical_assessment.structure_score:.1f}, "
        scratchpad_content += f"Clinical: {clinical_assessment.clinical_appropriateness:.1f}\n"
        scratchpad_content += f"Feedback: {clinical_assessment.feedback}"
        if clinical_assessment.suggestions:
            scratchpad_content += f"\nSuggestions: {'; '.join(clinical_assessment.suggestions)}"
        
        scratchpad_entry = ScratchpadEntry(
            agent=self.role,
            iteration=iteration,
            content=scratchpad_content
        )
        
        # Return updates to state
        return {
            "clinical_assessment": clinical_assessment,
            "scratchpad": [scratchpad_entry],
            "current_agent": self.role,
            "next_agent": AgentRole.SUPERVISOR,
            "needs_revision": needs_revision,
            "revision_reason": revision_reason,
            "messages": [{
                "role": "assistant",
                "content": f"Clinical Critic: Avg score {avg_score:.1f}/10"
            }]
        }
