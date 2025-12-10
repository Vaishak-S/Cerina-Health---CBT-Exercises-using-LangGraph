# Testing Guide - Cerina Protocol Foundry

## Prerequisites

Before testing, ensure you have:
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ installed  
- ✅ OpenAI API key set in `.env` file
- ✅ All dependencies installed

## Setup Steps

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=sk-...

# Initialize database (creates SQLite database)
python3 -c "from database.checkpointer import init_database; from database.history import init_history_db; init_database(); init_history_db()"
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Verify .env file exists
cat .env
# Should show: VITE_API_URL=http://localhost:8000
```

### 3. MCP Server Setup

```bash
cd mcp-server

# Install as editable package
pip install -e .
```

## Running the System

### Option A: Use Startup Script (macOS/Linux)

```bash
./start.sh
```

This will start both backend and frontend automatically.

### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Test Cases

### Test 1: Basic Protocol Generation (React UI)

**Steps:**
1. Open `http://localhost:5173` in browser
2. Enter user intent: `"Create a thought record exercise for anxiety"`
3. (Optional) Add context: `"Patient experiencing work-related stress"`
4. Click "Generate Protocol"

**Expected Results:**
- ✅ Protocol ID generated
- ✅ Agents appear in scratchpad in order:
  - Supervisor
  - Drafter
  - Safety Guardian
  - Clinical Critic
  - Supervisor (decision)
- ✅ Safety assessment shows (should be "SAFE")
- ✅ Clinical scores displayed (Empathy, Structure, Clinical)
- ✅ Current draft visible in text area
- ✅ "Human Review Required" panel appears
- ✅ Real-time updates via WebSocket

**Approval:**
- Click "✓ Approve Protocol"
- ✅ "Workflow Complete" message appears

### Test 2: Human Edits

**Steps:**
1. Generate a protocol (as in Test 1)
2. When human review appears, edit the draft text
3. Add feedback: `"Added more specific examples"`
4. Click "✓ Approve Protocol"

**Expected:**
- ✅ Edited version saved
- ✅ Workflow completes
- ✅ Database updated with edited version

### Test 3: Request Revision

**Steps:**
1. Generate a protocol
2. At human review, add feedback: `"Needs more empathetic language"`
3. Click "Request Revision"

**Expected:**
- ✅ Workflow resumes
- ✅ Drafter creates new version
- ✅ All agents re-evaluate
- ✅ New human review prompt appears

### Test 4: Safety Flag Detection

**Steps:**
1. Enter intent: `"Create an exercise for dealing with suicidal thoughts"`

**Expected:**
- ✅ Safety Guardian should flag concerns
- ✅ Drafter will revise to be safer
- ✅ Multiple iterations may occur
- ✅ Eventually reaches human approval

### Test 5: MCP Integration

**Setup:**
1. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python3",
      "args": [
        "/absolute/path/to/mcp-server/server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

2. Restart Claude Desktop

**Test:**
Ask Claude:
```
"Use the Cerina Foundry tool to create a sleep hygiene protocol for insomnia"
```

**Expected:**
- ✅ Tool appears in Claude's available tools
- ✅ Claude calls `generate_cbt_protocol`
- ✅ Backend workflow runs
- ✅ Final protocol returned to Claude
- ✅ Includes agent deliberation log
- ✅ Shows safety and clinical assessments

### Test 6: Persistence & Resume

**Steps:**
1. Start a protocol generation
2. While agents are working, kill the backend server (Ctrl+C)
3. Restart backend: `uvicorn main:app --reload`
4. Fetch state: `GET http://localhost:8000/api/protocols/{protocol_id}/state`

**Expected:**
- ✅ State preserved in database
- ✅ Can resume workflow
- ✅ All scratchpad entries intact

### Test 7: Multiple Iterations

**Steps:**
1. Generate protocol with intent: `"Create cognitive restructuring exercise"`
2. At human review, click "Request Revision" with feedback
3. Repeat 2-3 times

**Expected:**
- ✅ Iteration count increases
- ✅ Draft versions tracked
- ✅ Each agent's feedback visible
- ✅ After max iterations (5), forces human approval

### Test 8: API Endpoints

**Backend Health:**
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","service":"Cerina Protocol Foundry"}
```

**Create Protocol:**
```bash
curl -X POST http://localhost:8000/api/protocols \
  -H "Content-Type: application/json" \
  -d '{
    "user_intent": "Create a breathing exercise for panic attacks",
    "user_context": "Patient has history of panic disorder"
  }'
# Expected: {"protocol_id":"...","status":"processing","message":"..."}
```

**Get State:**
```bash
curl http://localhost:8000/api/protocols/{protocol_id}/state
# Expected: Full state JSON with scratchpad, assessments, etc.
```

**Submit Feedback:**
```bash
curl -X POST http://localhost:8000/api/protocols/{protocol_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "feedback": "Looks good!",
    "edits": null
  }'
```

## Database Verification

### Check SQLite Database

```bash
cd backend
sqlite3 cerina_foundry.db

# View tables
.tables
# Expected: checkpoint, protocol_history, agent_interactions, safety_logs

# View checkpoints
SELECT * FROM checkpoint LIMIT 5;

# View protocol history
SELECT id, user_intent, human_approved, completed_at FROM protocol_history;

# Exit
.quit
```

## Troubleshooting

### Backend won't start
- Check if port 8000 is in use: `lsof -i :8000`
- Verify virtual environment activated
- Check .env file exists with OPENAI_API_KEY

### Frontend won't connect
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check CORS settings in backend/.env
- Check browser console for errors

### MCP not working
- Verify absolute path in Claude config
- Check OPENAI_API_KEY in MCP env
- Restart Claude Desktop completely
- Check Claude Desktop logs: `~/Library/Logs/Claude/`

### WebSocket issues
- Check browser console for connection errors
- Verify backend WebSocket endpoint: `ws://localhost:8000/ws/{id}`
- Test with tool like `wscat`: `wscat -c ws://localhost:8000/ws/test-id`

### Database errors
- Delete and recreate: `rm backend/cerina_foundry.db` then reinitialize
- Check file permissions
- Verify SQLAlchemy version matches requirements

## Performance Metrics

Expected response times:
- **Initial draft creation**: 5-10 seconds
- **Safety evaluation**: 3-5 seconds
- **Clinical assessment**: 3-5 seconds
- **Full workflow (3-5 iterations)**: 30-60 seconds
- **MCP tool call**: 40-70 seconds

## Success Criteria

All tests should demonstrate:
- ✅ Multi-agent collaboration visible in real-time
- ✅ Safety and clinical assessments accurate
- ✅ Human-in-the-loop interrupt works reliably
- ✅ State persisted to database correctly
- ✅ MCP integration functional
- ✅ WebSocket streaming operational
- ✅ Crash recovery via checkpointing

## Video Recording Checklist

For Loom demo (5 min max):

**Segment 1: React UI (2 min)**
- [ ] Show homepage with input form
- [ ] Submit intent and watch agents work
- [ ] Highlight scratchpad entries
- [ ] Show safety/clinical assessments
- [ ] Demonstrate human approval interrupt
- [ ] Edit draft and approve
- [ ] Show completion message

**Segment 2: MCP Integration (1 min)**
- [ ] Show Claude Desktop with tool
- [ ] Trigger protocol generation
- [ ] Show returned result with agent log

**Segment 3: Code Walkthrough (2 min)**
- [ ] Show `models/state.py` - rich state structure
- [ ] Show `database/checkpointer.py` - persistence
- [ ] Show `graph/workflow.py` - routing logic
- [ ] Highlight interrupt mechanism

## Additional Test Ideas

- Test with different CBT modalities (exposure therapy, behavioral activation, etc.)
- Test edge cases (empty input, very long context)
- Load testing with multiple concurrent requests
- Test different safety scenarios (medical advice, self-harm content)
- Test quality thresholds (intentionally bad drafts)

## Cleanup

After testing:
```bash
# Stop servers
Ctrl+C (in both terminals)

# Optional: Clean database
rm backend/cerina_foundry.db
```
