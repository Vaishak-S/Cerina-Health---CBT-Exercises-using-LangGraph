"""
Safety Guardian Agent: Checks drafts for safety concerns and harmful content.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from ..models.state import ProtocolState, AgentRole, ScratchpadEntry, SafetyAssessment, SafetyLevel
import json


class SafetyGuardianAgent:
    """Agent responsible for safety evaluation"""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.3):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.role = AgentRole.SAFETY_GUARDIAN
        self.parser = JsonOutputParser()
        
    def create_system_prompt(self) -> str:
        """Create system prompt for safety evaluation"""
        return """You are a Safety Guardian for CBT therapeutic exercises.
Your role is to identify any safety concerns in the draft exercise.

Check for:
1. **Self-harm risk**: Content that could encourage or trigger self-harm
2. **Medical advice**: Unauthorized medical diagnoses or prescriptions
3. **Crisis situations**: Content inappropriate for active crisis situations
4. **Triggering content**: Potentially triggering descriptions without warnings
5. **Harmful techniques**: Non-evidence-based or potentially harmful methods
6. **Boundary violations**: Inappropriate therapeutic boundaries

IMPORTANT: You MUST respond with ONLY a valid JSON object. Do not include any other text.

JSON format:
{
    "level": "safe" | "needs_review" | "unsafe",
    "concerns": ["list of specific concerns, or empty array if none"],
    "recommendations": ["specific fixes needed, or empty array if none"],
    "flagged_lines": []
}

Example for a safe exercise:
{
    "level": "safe",
    "concerns": [],
    "recommendations": [],
    "flagged_lines": []
}

Example for concerns:
{
    "level": "needs_review",
    "concerns": ["Exercise lacks warning about when to seek professional help"],
    "recommendations": ["Add disclaimer about seeking professional support if anxiety worsens"],
    "flagged_lines": []
}
"""
    
    def __call__(self, state: ProtocolState) -> Dict[str, Any]:
        """Execute the safety guardian agent"""
        print(f"[SAFETY_GUARDIAN] Starting safety evaluation")
        iteration = state["iteration_count"]
        current_draft = state["current_draft"]
        
        # Create evaluation prompt
        system_prompt = self.create_system_prompt()
        user_message = f"""Evaluate this CBT exercise draft for safety:

{current_draft}

Provide your safety assessment as JSON."""
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        
        print(f"[SAFETY_GUARDIAN] Raw LLM response (first 200 chars): {response.content[:200]}")
        
        # Parse JSON response
        try:
            # Try to extract JSON from markdown code blocks if present
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            assessment_data = json.loads(content)
            print(f"[SAFETY_GUARDIAN] Successfully parsed JSON: level={assessment_data.get('level')}")
        except Exception as e:
            # Fallback if parsing fails
            print(f"[SAFETY_GUARDIAN] JSON parse error: {e}")
            print(f"[SAFETY_GUARDIAN] Content to parse: {response.content[:500]}")
            assessment_data = {
                "level": "needs_review",
                "concerns": [f"Unable to parse safety assessment: {str(e)}"],
                "recommendations": ["Manual review required"],
                "flagged_lines": []
            }
        
        # Create safety assessment
        safety_assessment = SafetyAssessment(
            level=SafetyLevel(assessment_data["level"]),
            concerns=assessment_data.get("concerns", []),
            recommendations=assessment_data.get("recommendations", []),
            flagged_lines=assessment_data.get("flagged_lines", [])
        )
        
        # Create scratchpad entry
        scratchpad_content = f"Safety Level: {safety_assessment.level.value}"
        if safety_assessment.concerns:
            scratchpad_content += f"\nConcerns: {'; '.join(safety_assessment.concerns)}"
        if safety_assessment.recommendations:
            scratchpad_content += f"\nRecommendations: {'; '.join(safety_assessment.recommendations)}"
        
        scratchpad_entry = ScratchpadEntry(
            agent=self.role,
            iteration=iteration,
            content=scratchpad_content
        )
        
        # Determine if revision is needed
        needs_revision = safety_assessment.level != SafetyLevel.SAFE
        revision_reason = None
        if needs_revision:
            revision_reason = f"Safety concerns identified: {'; '.join(safety_assessment.concerns)}"
        
        print(f"[SAFETY_GUARDIAN] Completed - level={safety_assessment.level.value}, needs_revision={needs_revision}")
        
        # Return updates to state
        return {
            "safety_assessment": safety_assessment,
            "scratchpad": [scratchpad_entry],
            "current_agent": self.role,
            "next_agent": AgentRole.SUPERVISOR if needs_revision else AgentRole.CLINICAL_CRITIC,
            "needs_revision": needs_revision,
            "revision_reason": revision_reason,
            "messages": [{
                "role": "assistant",
                "content": f"Safety Guardian: {safety_assessment.level.value}"
            }]
        }
