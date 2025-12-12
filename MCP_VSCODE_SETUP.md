# MCP Integration with VS Code - Setup Guide

## ✅ What's Already Done

1. ✅ Claude Code extension installed
2. ✅ MCP configuration files created
3. ✅ VS Code settings configured

## 🔧 What You Need To Do

### Step 1: Add Your OpenAI API Key

Edit `.vscode/mcp-settings.json` and replace `YOUR_OPENAI_API_KEY_HERE` with your actual OpenAI API key.

### Step 2: Test the MCP Server

1. Make sure the backend PostgreSQL database is running:
   ```bash
   # Check if PostgreSQL is running
   psql -U postgres -c "SELECT 1"
   ```

2. Test the MCP server standalone:
   ```bash
   cd mcp-server
   python server.py
   ```

### Step 3: Use the MCP Tool in VS Code

1. Open the Claude Code panel in VS Code (click the Claude icon in the sidebar)
2. Start a new chat
3. You should see "cerina-foundry" tool available
4. Try asking: "Use the cerina-foundry tool to create a CBT exercise for managing social anxiety"

## 🎯 Example Prompts

Once connected, try these:

```
"Use cerina-foundry to create a sleep hygiene protocol for insomnia"

"Ask Cerina Foundry to generate a CBT exercise for public speaking anxiety"

"Create an exposure hierarchy for agoraphobia using the cerina-foundry tool"
```

## 🔍 Troubleshooting

**Tool not appearing:**
- Reload VS Code window (Cmd+Shift+P → "Reload Window")
- Check the Output panel (View → Output) and select "Claude Code" to see logs

**Connection errors:**
- Ensure backend PostgreSQL is running
- Check that OPENAI_API_KEY is set in `.vscode/mcp-settings.json`
- Verify DATABASE_URL is correct

**Server not starting:**
- Check Python dependencies: `pip install mcp httpx`
- Verify server.py path in mcp-settings.json is correct

## 📚 What the Tool Does

The `generate_cbt_protocol` tool:
- Takes `user_intent` (required) and `user_context` (optional)
- Runs the full multi-agent workflow (Supervisor → Drafter → Safety → Clinical → Human Approval)
- Returns a CBT exercise protocol ID
- You can then view the full protocol in the React UI at http://localhost:5173

## 🎬 Next Steps

After testing the MCP integration:
1. Create the architecture diagram
2. Record the Loom video showing:
   - React UI with agents working
   - MCP tool being used in VS Code
   - Code walkthrough of state management
