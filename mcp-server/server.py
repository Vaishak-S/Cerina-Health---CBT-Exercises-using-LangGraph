"""
MCP Server for Cerina Protocol Foundry.
Exposes the LangGraph workflow as an MCP tool/resource.
"""
import asyncio
import sys
import os
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types
import httpx

# Add parent directory to path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.graph.workflow import create_graph, create_initial_state
from backend.database.checkpointer import init_database


# Initialize server
app = Server("cerina-foundry")

# Initialize database and graph
checkpointer = init_database()
graph = create_graph(checkpointer)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="generate_cbt_protocol",
            description="""Generate a CBT (Cognitive Behavioral Therapy) exercise protocol.
            
This tool uses a multi-agent system to autonomously design, critique, and refine
therapeutic exercises. The system includes:
- Drafter: Creates structured CBT exercises
- Safety Guardian: Checks for safety concerns
- Clinical Critic: Evaluates empathy and clinical quality
- Supervisor: Orchestrates the workflow

The process includes multiple iterations of refinement before producing a final protocol.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_intent": {
                        "type": "string",
                        "description": "The therapeutic goal or intent (e.g., 'Create an exposure hierarchy for agoraphobia')"
                    },
                    "user_context": {
                        "type": "string",
                        "description": "Optional additional context about the patient or situation"
                    }
                },
                "required": ["user_intent"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls"""
    if name != "generate_cbt_protocol":
        raise ValueError(f"Unknown tool: {name}")
    
    user_intent = arguments.get("user_intent")
    user_context = arguments.get("user_context")
    
    if not user_intent:
        raise ValueError("user_intent is required")
    
    # Generate unique thread ID
    import uuid
    thread_id = str(uuid.uuid4())
    
    # Create initial state
    initial_state = create_initial_state(user_intent, user_context)
    
    # Run workflow
    config = {"configurable": {"thread_id": thread_id}}
    
    result_text = f"# CBT Protocol Generation\n\n**Intent:** {user_intent}\n\n"
    if user_context:
        result_text += f"**Context:** {user_context}\n\n"
    
    result_text += "## Agent Deliberation\n\n"
    
    final_state = None
    iteration_count = 0
    
    try:
        # Run until human approval interrupt
        async for event in graph.astream(initial_state, config, stream_mode="values"):
            final_state = event
            iteration_count += 1
            
            # Add scratchpad entries to result
            if event.get("scratchpad"):
                for entry in event["scratchpad"][-1:]:  # Show latest entry
                    result_text += f"**{entry.agent.value.upper()}** (Iteration {entry.iteration}): {entry.content}\n\n"
            
            # Check if we need human approval
            if event.get("requires_human_approval"):
                result_text += "---\n\n## Draft Protocol\n\n"
                result_text += event.get("current_draft", "")
                result_text += "\n\n---\n\n"
                
                # Auto-approve for MCP (since no human in the loop here)
                result_text += "*Note: In MCP mode, protocol is auto-approved. Use the React UI for human-in-the-loop review.*\n\n"
                
                # Update state to approve
                await graph.aupdate_state(
                    config,
                    {"human_approved": True, "completed": True}
                )
                
                # Get final state
                final_state_obj = await graph.aget_state(config)
                final_state = final_state_obj.values
                break
            
            # Prevent infinite loops
            if iteration_count > 20:
                result_text += "\n\n*Maximum iterations reached. Workflow terminated.*\n"
                break
        
        # Add final protocol
        if final_state and final_state.get("final_protocol"):
            result_text += "## Final Protocol\n\n"
            result_text += final_state["final_protocol"]
        elif final_state and final_state.get("current_draft"):
            result_text += "## Final Protocol\n\n"
            result_text += final_state["current_draft"]
        
        # Add assessments
        if final_state and final_state.get("safety_assessment"):
            safety = final_state["safety_assessment"]
            result_text += f"\n\n### Safety Assessment\n- Level: {safety.level.value}\n"
            if safety.concerns:
                result_text += f"- Concerns: {', '.join(safety.concerns)}\n"
        
        if final_state and final_state.get("clinical_assessment"):
            clinical = final_state["clinical_assessment"]
            result_text += f"\n### Clinical Quality\n"
            result_text += f"- Empathy: {clinical.empathy_score}/10\n"
            result_text += f"- Structure: {clinical.structure_score}/10\n"
            result_text += f"- Clinical Appropriateness: {clinical.clinical_appropriateness}/10\n"
    
    except Exception as e:
        result_text += f"\n\n**Error:** {str(e)}\n"
    
    return [types.TextContent(type="text", text=result_text)]


@app.list_resources()
async def list_resources() -> list[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="cerina://protocols/latest",
            name="Latest Protocol",
            description="The most recently generated CBT protocol",
            mimeType="text/markdown"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource"""
    if uri == "cerina://protocols/latest":
        # Return info about the MCP server
        return """# Cerina Protocol Foundry

This is an MCP server that provides access to a multi-agent CBT protocol generation system.

## Available Tool

**generate_cbt_protocol**: Generate therapeutic CBT exercises using an autonomous multi-agent system.

## Example Usage

```
Use the generate_cbt_protocol tool with:
- user_intent: "Create a thought record exercise for anxiety"
- user_context: "Patient experiencing work-related stress"
```

The system will automatically:
1. Draft an initial protocol
2. Check for safety concerns
3. Evaluate clinical quality
4. Refine based on feedback
5. Return a polished, safe, and empathetic CBT exercise
"""
    raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cerina-foundry",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
