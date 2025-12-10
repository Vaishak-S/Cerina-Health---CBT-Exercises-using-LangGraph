# Cerina Protocol Foundry - MCP Server

This is a Model Context Protocol (MCP) server that exposes the Cerina Protocol Foundry multi-agent system as a tool that can be used by MCP clients like Claude Desktop.

## Installation

1. Install dependencies:
```bash
pip install -e .
```

2. Make sure the backend is set up with required environment variables.

## Configuration for Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": [
        "/path/to/Cerina Health Project/mcp-server/server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Usage

Once configured, you can ask Claude Desktop:

- "Use the Cerina Foundry to create a sleep hygiene protocol"
- "Generate a CBT exercise for managing social anxiety"
- "Create an exposure hierarchy for agoraphobia"

The MCP server will:
1. Trigger the multi-agent backend
2. Run the autonomous workflow
3. Return the refined CBT protocol

## Available Tool

**generate_cbt_protocol**
- Input: `user_intent` (required), `user_context` (optional)
- Output: Fully refined CBT exercise protocol with safety and clinical assessments
