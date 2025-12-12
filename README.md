# Cerina Protocol Foundry

> **An intelligent multi-agent system for autonomously designing, critiquing, and refining CBT (Cognitive Behavioral Therapy) exercises.**

Built as the "Agentic Architect Sprint" - a complete implementation of a clinical review system that mimics rigorous medical oversight through autonomous AI agents.

## 🎯 What This System Does

The Cerina Protocol Foundry is a **multi-agent autonomous system** that:
1. Accepts user intent (e.g., "Create an exposure hierarchy for agoraphobia")
2. Generates CBT exercise protocols through **autonomous agent deliberation**
3. Self-corrects and iterates internally before requiring human oversight
4. Interrupts for **human-in-the-loop approval** at critical checkpoints
5. Exposes functionality through both **React UI** and **MCP protocol**

## 🏗️ Architecture Overview

### Multi-Agent System (Supervisor-Worker Pattern)

**Four Specialized Agents:**
- **Supervisor Agent**: Central orchestrator that routes tasks, evaluates draft readiness, and manages workflow state
- **Drafter Agent**: Generates and revises CBT exercises using GPT-4, responds to feedback from other agents
- **Safety Guardian**: Clinical safety evaluator checking for self-harm risks, medical advice, and triggering content
- **Clinical Critic**: Quality assessor measuring empathy (1-10), structure (1-10), and clinical appropriateness (1-10)

**Architecture Pattern:** Supervisor-Worker with autonomous iteration loops
- Agents communicate through a shared "blackboard" state
- Supervisor decides routing based on draft status, safety, and quality scores
- System loops internally until clinical quality threshold met (8.0/10 average)
- Interrupts at `human_approval` checkpoint for final review

### Key Features

✅ **Autonomous Iteration**: Agents debate and refine internally - may cycle through multiple drafts without human intervention  
✅ **Rich State Management**: Structured "blackboard" with agent scratchpads, version tracking, assessments, and metadata  
✅ **Persistent Checkpointing**: PostgreSQL-backed state persistence - resume from exact point after crashes  
✅ **Human-in-the-Loop**: Interrupt mechanism with approval/revision workflow - humans have final say  
✅ **Real-time Visualization**: React UI shows agents working live with 2-second polling updates  
✅ **MCP Integration**: Full Model Context Protocol server - expose workflow as tool for VS Code, Claude Desktop, etc.  

## 📦 Tech Stack

**Backend:**
- **LangGraph 0.2.62**: Multi-agent orchestration with state management
- **FastAPI**: REST API server for protocol management
- **PostgreSQL**: Persistent checkpointing with PostgresSaver (sync)
- **OpenAI GPT-4**: LLM for agent reasoning and content generation
- **Python 3.10+**: Core language

**Frontend:**
- **React 18** + **TypeScript**: UI framework
- **Vite**: Build tool and dev server
- **CSS3**: Styling with animations

**MCP Integration:**
- **mcp-python SDK**: Model Context Protocol server
- **Stdio transport**: VS Code and Claude Desktop integration

**Database Schema:**
- `checkpoints` table: LangGraph state snapshots
- `checkpoint_writes` table: State update history
- State includes: drafts, assessments, agent scratchpads, iteration counts

## 🚀 Complete Deployment Guide

### Prerequisites

```bash
# Check versions
python --version  # Need 3.10+
node --version    # Need 18+
psql --version    # PostgreSQL 14+
```

### Step 1: Clone and Setup Project

```bash
# Navigate to project directory
cd "Cerina Health Project"

# Project structure should look like:
# backend/       - FastAPI + LangGraph
# frontend/      - React + TypeScript
# mcp-server/    - MCP protocol server
```

### Quick Setup Option (Automated)

For rapid setup, use the provided automation scripts:

```bash
# Option 1: Automated setup (recommended for first-time setup)
chmod +x setup.sh
./setup.sh
# This will:
# - Check Python and Node.js versions
# - Create virtual environment
# - Install all dependencies
# - Copy .env.example to .env (you'll need to add your API key)

# Option 2: Start all services with one command
chmod +x start.sh
./start.sh
# This will:
# - Start backend on http://localhost:8000
# - Start frontend on http://localhost:5173
# - Run both in background
```

**Important:** After running `setup.sh`, edit `backend/.env` and add your OpenAI API key:
```bash
nano backend/.env
# Add: OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Manual Setup (Step-by-Step)

If you prefer manual setup or the scripts don't work on your system:

### Step 2: PostgreSQL Database Setup

```bash
# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@14

# Or on Linux
sudo systemctl start postgresql

# Create database
psql -U postgres -c "CREATE DATABASE cerina_foundry;"

# Verify database exists
psql -U postgres -c "\l" | grep cerina_foundry
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Expected packages:
# - langgraph==0.2.62
# - langchain-openai
# - fastapi
# - uvicorn
# - psycopg[binary,pool]
# - python-dotenv
# - pydantic

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use any editor
```

**.env Configuration:**
```bash
# Required: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Database (update if using different credentials)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cerina_foundry

# API Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
HOST=0.0.0.0
PORT=8000
```

```bash
# Initialize database tables (LangGraph checkpointer)
python -c "from database.checkpointer import init_database; init_database()"

# You should see:
# "Database initialized successfully"
# "Tables: checkpoints, checkpoint_writes"

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Backend running at: http://localhost:8000
# API docs available at: http://localhost:8000/docs
```

### Step 4: Frontend Setup

```bash
# Open new terminal, navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Expected packages:
# - react, react-dom
# - typescript
# - vite
# - @vitejs/plugin-react

# Start development server
npm run dev

# Frontend running at: http://localhost:5173
# Vite will show the exact URL in terminal
```

### Step 5: MCP Server Setup (Optional - for VS Code Integration)

```bash
cd mcp-server

# Install MCP dependencies in backend venv
source ../backend/venv/bin/activate
pip install mcp httpx

# Test MCP server standalone
python server.py
# Press Ctrl+C to stop after verifying it starts

# For VS Code integration:
# 1. Install Claude Code extension in VS Code
# 2. Open VS Code settings (Cmd+,)
# 3. Search for "MCP"
# 4. Add server configuration (see MCP_VSCODE_SETUP.md)
```

**MCP Configuration for VS Code:**

Create or edit `~/Library/Application Support/Code/User/mcp.json`:
```json
{
  "servers": {
    "cerina-foundry": {
      "type": "stdio",
      "command": "/path/to/python",
      "args": ["/absolute/path/to/mcp-server/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/cerina_foundry"
      }
    }
  }
}
```

### Step 6: Verify Everything Works

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
# Should show: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Should show: Local: http://localhost:5173
```

**Test the System:**

1. **Open Browser**: Navigate to `http://localhost:5173`
2. **Create Protocol**: 
   - Enter user intent: "Create a CBT exercise for managing anxiety"
   - Click "Generate Protocol"
3. **Watch Agents Work**:
   - See Supervisor routing decisions
   - See Drafter generating content
   - See Safety Guardian evaluation
   - See Clinical Critic assessment
4. **Human Approval**:
   - When prompted, click "Approve Protocol" or "Request Revision"
5. **Verify Database**:
   ```bash
   psql -U postgres cerina_foundry -c "SELECT COUNT(*) FROM checkpoints;"
   ```

## 🎯 Usage Guide

### Via React UI (Primary Interface)

1. **Access UI**: Open `http://localhost:5173`
2. **Enter Intent**: Type your therapeutic goal
   ```
   "Create an exposure hierarchy for agoraphobia"
   "Design a sleep hygiene protocol for insomnia"
   "Build a thought record exercise for anxiety"
   ```
3. **Watch Deliberation**: See agents work in real-time
   - **Supervisor**: Routes between agents based on state
   - **Drafter**: Generates protocol drafts
   - **Safety Guardian**: Evaluates safety (safe/caution/unsafe)
   - **Clinical Critic**: Scores empathy, structure, clinical quality
4. **Agent Scratchpad**: View agent-to-agent communication
5. **Human Checkpoint**: System interrupts for your approval
6. **Approve or Revise**:
   - **Approve**: Saves final protocol to database
   - **Request Revision**: Provide feedback, agents rework the draft

### Via MCP (VS Code / Claude Desktop)

Once configured in VS Code:

1. **Open Claude Chat** in VS Code
2. **Invoke Tool**: 
   ```
   "Use cerina-foundry to create a CBT exercise for social anxiety"
   ```
3. **View Results**: Protocol generated and returned in chat
4. **Access Full Details**: Check React UI at `http://localhost:5173` for protocol details

### Via REST API (Programmatic)

```bash
# Create new protocol
curl -X POST http://localhost:8000/api/protocols \
  -H "Content-Type: application/json" \
  -d '{"user_intent": "Create a mindfulness exercise for stress"}'

# Response: {"protocol_id": "uuid-here", "status": "processing"}

# Check status
curl http://localhost:8000/api/protocols/{protocol_id}/state

# Submit approval
curl -X POST http://localhost:8000/api/protocols/{protocol_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

## 📊 API Endpoints

### REST API (FastAPI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/protocols` | Create new protocol generation request |
| GET | `/api/protocols/{id}/state` | Get current workflow state and draft |
| POST | `/api/protocols/{id}/feedback` | Submit human approval or revision feedback |
| GET | `/api/health` | Health check - verify backend is running |
| GET | `/docs` | Interactive API documentation (Swagger) |
| WS | `/ws/{protocol_id}` | WebSocket for real-time state updates (optional) |

**Example Requests:**

```bash
# 1. Create Protocol
POST /api/protocols
{
  "user_intent": "Create a CBT exercise for managing anxiety",
  "user_context": "Patient has work-related stress" # optional
}

# Response:
{
  "protocol_id": "uuid-here",
  "status": "processing",
  "message": "Protocol generation started"
}

# 2. Check State (poll every 2 seconds)
GET /api/protocols/{protocol_id}/state

# Response includes:
{
  "protocol_id": "uuid",
  "current_draft": "Full CBT exercise text...",
  "safety_assessment": {
    "level": "safe",
    "concerns": []
  },
  "clinical_assessment": {
    "empathy_score": 9.0,
    "structure_score": 8.5,
    "clinical_appropriateness": 9.0
  },
  "scratchpad": [
    {"agent": "supervisor", "content": "Routing to Drafter..."},
    {"agent": "drafter", "content": "Generated draft..."}
  ],
  "iteration_count": 4,
  "requires_human_approval": true,
  "completed": false
}

# 3. Approve Protocol
POST /api/protocols/{protocol_id}/feedback
{
  "approved": true
}

# 4. Request Revision
POST /api/protocols/{protocol_id}/feedback
{
  "approved": false,
  "feedback": "Add more examples and make it more specific to work anxiety"
}
```

### MCP Tools

**Tool:** `generate_cbt_protocol`

**Input Schema:**
```json
{
  "user_intent": "string (required)",
  "user_context": "string (optional)"
}
```

**Output:** Markdown-formatted protocol with:
- Generated CBT exercise
- Agent workflow log
- Safety assessment
- Clinical quality scores
- Protocol ID for further review in UI

**Usage in VS Code:**
```
"Create a CBT protocol for overcoming stage fright before office presentations"
```

## 🗂️ Project Structure

```
Cerina Health Project/
├── backend/                      # FastAPI + LangGraph Backend
│   ├── agents/                   # Agent Implementations
│   │   ├── __init__.py
│   │   ├── supervisor.py         # Orchestrator - routes workflow
│   │   ├── drafter.py            # Content generator using GPT-4
│   │   ├── safety_guardian.py    # Safety evaluator
│   │   └── clinical_critic.py    # Quality assessor
│   ├── database/                 # Persistence Layer
│   │   ├── __init__.py
│   │   ├── checkpointer.py       # PostgresSaver setup
│   │   └── history.py            # Protocol history (unused in final)
│   ├── graph/                    # LangGraph Workflow
│   │   ├── __init__.py
│   │   └── workflow.py           # StateGraph definition, routing
│   ├── models/                   # State Definitions
│   │   ├── __init__.py
│   │   └── state.py              # ProtocolState TypedDict
│   ├── main.py                   # FastAPI application entry
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment template
│   └── .env                      # Your config (gitignored)
│
├── frontend/                     # React + TypeScript UI
│   ├── src/
│   │   ├── App.tsx               # Main component with polling
│   │   ├── App.css               # Styling + animations
│   │   ├── main.tsx              # React entry point
│   │   └── vite-env.d.ts         # TypeScript definitions
│   ├── public/                   # Static assets
│   ├── index.html                # HTML template
│   ├── package.json              # Node dependencies
│   ├── vite.config.ts            # Vite configuration
│   ├── tsconfig.json             # TypeScript config
│   └── tsconfig.app.json         # App-specific TS config
│
├── mcp-server/                   # Model Context Protocol Server
│   ├── server.py                 # MCP stdio server implementation
│   ├── pyproject.toml            # MCP package config
│   └── README.md                 # MCP-specific docs
│
├── README.md                     # This file - complete guide
├── ARCHITECTURE.md               # Technical architecture details
├── QUICKSTART.md                 # Quick start guide
├── MCP_VSCODE_SETUP.md          # VS Code MCP integration guide
├── FINAL_SUBMISSION.md          # Submission summary
├── TESTING.md                    # Testing guide
├── Task.txt                      # Original requirements
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment template (root level)
├── setup.sh                      # Automated setup script
├── start.sh                      # Start all services script
├── test_mcp.py                   # MCP test script
├── run_protocol.py               # CLI protocol generator
└── venv/                         # Python virtual environment (after setup)
```

### Key Files Explained

**Backend:**
- `backend/models/state.py`: Defines `ProtocolState` TypedDict with 20+ fields including drafts, scratchpads, assessments
- `backend/graph/workflow.py`: Creates StateGraph with 5 nodes (supervisor, drafter, safety, clinical, human_approval)
- `backend/database/checkpointer.py`: Initializes PostgresSaver for state persistence
- `backend/agents/supervisor.py`: Routing logic - checks `needs_revision`, draft status, safety, clinical scores
- `backend/agents/drafter.py`: Generates CBT content, clears human feedback flags after draft
- `backend/main.py`: FastAPI routes for protocol CRUD and human feedback

**Frontend:**
- `frontend/src/App.tsx`: 2-second polling, displays scratchpad, handles approve/revision
- `frontend/src/App.css`: Grid layout, agent badges, animations for state transitions

**MCP:**
- `mcp-server/server.py`: Stdio MCP server, exposes `generate_cbt_protocol` tool, uses ThreadPoolExecutor for sync graph

### State Flow

1. **User submits intent** → `POST /api/protocols` → Creates initial state with `user_intent`
2. **Backend starts workflow** → `graph.invoke()` → Enters Supervisor
3. **Supervisor routes** → Checks state → Routes to Drafter/Safety/Clinical/HumanApproval
4. **Agents update state** → Add scratchpad entries, set assessments, increment iterations
5. **Interrupt at human_approval** → `interrupt_before=["human_approval"]` → Checkpoint saved
6. **Frontend polls state** → `GET /api/protocols/{id}/state` → Displays current draft
7. **Human responds** → `POST /api/protocols/{id}/feedback` → Sets `human_approved` or `needs_revision`
8. **Workflow resumes** → Continues from checkpoint → Either completes or routes back to Drafter

## 🧪 Testing & Verification

### Manual Testing Flow

1. **Start Services:**
   ```bash
   # Terminal 1
   cd backend && source venv/bin/activate && uvicorn main:app --reload
   
   # Terminal 2
   cd frontend && npm run dev
   ```

2. **Test Protocol Generation:**
   - Open `http://localhost:5173`
   - Enter: "Create a CBT exercise for managing work stress"
   - Verify agents appear in sequence
   - Check scratchpad updates in real-time

3. **Test Human Approval:**
   - Wait for "Awaiting Human Approval" status
   - Click "Approve Protocol"
   - Verify `completed=true` in state
   - Check database: `psql -U postgres cerina_foundry -c "SELECT * FROM checkpoints ORDER BY checkpoint_id DESC LIMIT 1;"`

4. **Test Revision Flow:**
   - Generate new protocol
   - At approval checkpoint, provide feedback: "Add more specific examples"
   - Click "Request Revision"
   - Verify workflow routes back to Drafter
   - Check iteration count increases
   - Verify new draft appears with requested changes

5. **Test MCP Integration:**
   ```bash
   # Ensure environment variables are set
   export OPENAI_API_KEY=your_api_key_here
   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cerina_foundry
   
   # Run MCP test
   python test_mcp.py
   ```
   - Should connect to server
   - List available tools
   - Execute `generate_cbt_protocol`
   - Return formatted protocol
   
   **Note:** Both `test_mcp.py` and `run_protocol.py` now use environment variables for API keys instead of hardcoded values. Make sure your `.env` file is properly configured or export the variables before running these scripts.

### Database Verification

```bash
# Connect to database
psql -U postgres cerina_foundry

# Check tables exist
\dt

# View checkpoints
SELECT 
  checkpoint_id, 
  thread_id, 
  checkpoint_ns,
  channel_values::jsonb->'iteration_count' as iteration
FROM checkpoints 
ORDER BY checkpoint_id DESC 
LIMIT 5;

# View checkpoint writes
SELECT * FROM checkpoint_writes 
ORDER BY checkpoint_id DESC 
LIMIT 10;

# Exit
\q
```

### Expected Behavior

**Successful Flow:**
1. Supervisor → Drafter (iteration 1)
2. Supervisor → Safety Guardian (iteration 2)  
3. Supervisor → Clinical Critic (iteration 3)
4. Supervisor → Human Approval (iteration 4)
5. Human approves → Workflow completes

**Revision Flow:**
1. Human requests revision with feedback
2. Workflow updates `needs_revision=true`
3. Clears safety/clinical assessments
4. Supervisor → Drafter (new iteration)
5. Drafter generates new draft based on feedback
6. Repeats evaluation cycle
7. Returns to human approval

### Troubleshooting

**Backend not starting:**
```bash
# Check PostgreSQL running
pg_isready -h localhost

# Check database exists
psql -U postgres -l | grep cerina_foundry

# Verify Python dependencies
pip list | grep -E "langgraph|fastapi|psycopg"

# Check .env file exists and has OPENAI_API_KEY
cat backend/.env
```

**Frontend not connecting:**
```bash
# Verify backend running
curl http://localhost:8000/docs

# Check CORS settings in backend/.env
# Should include: CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Clear browser cache and reload
```

**MCP server not working:**
```bash
# Test Python path
which python

# Verify MCP dependencies
pip list | grep mcp

# Check environment variables in mcp.json
# Ensure OPENAI_API_KEY and DATABASE_URL are set correctly

# Test server directly
cd mcp-server && python server.py
# Should start without errors (use Ctrl+C to stop)
```

**Agents looping infinitely:**
- Check `backend/agents/supervisor.py` - `needs_revision` should be checked first
- Check `backend/agents/drafter.py` - Should clear `human_approved`, `human_feedback`, `needs_revision` flags
- Verify database has latest code: restart backend after code changes

## 🔍 State Management Deep Dive

### The "Blackboard" Architecture

The system uses a rich `ProtocolState` TypedDict shared across all agents:

**Core Fields:**
```python
user_intent: str              # User's therapeutic goal
user_context: str | None      # Additional patient context
current_draft: str | None     # Latest CBT exercise text
draft_versions: list[dict]    # History of all drafts

# Agent Communication
scratchpad: list[ScratchpadEntry]  # Agent notes & decisions
  # Each entry: {agent, content, timestamp, iteration}

# Quality Assessments
safety_assessment: SafetyLevel | None
  # {level: safe|caution|unsafe, concerns: [], recommendations: []}
clinical_assessment: ClinicalAssessment | None
  # {empathy_score, structure_score, clinical_appropriateness, feedback}

# Workflow Control
iteration_count: int          # How many agent passes
max_iterations: int           # Limit before force-stop
current_agent: AgentType      # Who's active now
next_agent: AgentType | None  # Where to route next

# Human Interaction Flags
needs_revision: bool          # Human requested changes
revision_reason: str | None   # Human's feedback text
requires_human_approval: bool # Interrupt signal
human_approved: bool | None   # Human's decision
human_feedback: str | None    # Human's input
human_edits: str | None       # Direct edits to text

# Completion
final_protocol: str | None    # Approved final version
completed: bool               # Workflow finished
messages: list[BaseMessage]   # LangChain message history
```

### How Agents Use State

**Supervisor:**
```python
if state["needs_revision"]:
    return "drafter"  # Priority: handle human feedback first
elif not state["current_draft"]:
    return "drafter"  # No draft yet
elif not state["safety_assessment"]:
    return "safety_guardian"  # Safety check needed
elif not state["clinical_assessment"]:
    return "clinical_critic"  # Quality check needed
elif clinical_avg >= 8.0:
    return "human_approval"  # Good enough for human review
else:
    return "drafter"  # Needs improvement
```

**Drafter:**
```python
# Read from state
previous_draft = state["current_draft"]
safety_concerns = state["safety_assessment"]["concerns"]
clinical_feedback = state["clinical_assessment"]["feedback"]
human_feedback = state["human_feedback"]

# Generate new draft with context
new_draft = llm.invoke(prompt_with_all_context)

# Write to state
return {
    "current_draft": new_draft,
    "draft_versions": [...old_versions, {"draft": new_draft, "iteration": n}],
    "scratchpad": [..., {"agent": "drafter", "content": "Generated draft..."}],
    "needs_revision": False,  # Clear revision flag
    "human_approved": None,    # Clear approval flag
    "human_feedback": None     # Clear feedback
}
```

### Checkpointing Mechanism

**What Gets Saved:**
- Entire `ProtocolState` after each agent execution
- Captured as JSONB in PostgreSQL `checkpoints` table
- Thread ID = Protocol ID (UUID)
- Each checkpoint has namespace (e.g., "supervisor", "drafter")

**Resume Logic:**
```python
# Get last checkpoint
checkpoint = checkpointer.get(thread_id)

# Resume workflow from that state
final_state = graph.invoke(None, {
    "configurable": {"thread_id": thread_id}
})
# LangGraph automatically loads from checkpoint
```

**When Checkpoints Are Created:**
1. After every agent node execution
2. Before interrupt (at `human_approval` node)
3. After human feedback processed
4. On workflow completion

## 🛡️ Safety & Clinical Quality System

### Safety Guardian Evaluation

**Safety Levels:**
- `safe`: No concerns, ready for use
- `caution`: Minor issues, review recommended
- `unsafe`: Critical issues, must be revised

**Evaluation Criteria:**
```python
concerns_to_check = [
    "self-harm or suicide ideation",
    "medical advice beyond scope",
    "inappropriate power dynamics",
    "unvalidated treatment claims",
    "triggering/graphic content",
    "inadequate crisis resources"
]
```

**LLM Prompt Structure:**
```
You are a clinical safety reviewer. Evaluate this CBT exercise for:
1. Risk of harm (self-harm, medical advice)
2. Ethical concerns (power dynamics, consent)
3. Clinical appropriateness (evidence-based, scope)

Return JSON:
{
  "level": "safe" | "caution" | "unsafe",
  "concerns": ["specific issue 1", ...],
  "recommendations": ["how to fix 1", ...],
  "flagged_lines": [{"line": 3, "issue": "..."}]
}
```

### Clinical Critic Assessment

**Scoring Dimensions (1-10):**
1. **Empathy**: Validates patient experience, non-judgmental tone
2. **Structure**: Clear steps, logical flow, actionable guidance
3. **Clinical Appropriateness**: Evidence-based, ethical, within CBT scope

**Quality Threshold:**
- Average score ≥ 8.0 → Ready for human approval
- Average score < 8.0 → Routes back to Drafter for improvement

**Feedback Loop:**
```python
if clinical_avg < 8.0:
    # Drafter receives specific feedback
    drafter_prompt += f"""
    Previous draft scored {clinical_avg}/10.
    Clinical feedback: {clinical_assessment.feedback}
    
    Improvements needed:
    - Empathy: {empathy_score}/10
    - Structure: {structure_score}/10
    - Clinical: {clinical_appropriateness}/10
    """
```

## 🎥 Demo & Submission

### Loom Video Structure (5 minutes)

**Minute 1-2: React UI Demo**
- Show protocol creation form
- Watch agents deliberate in real-time
- Point out scratchpad entries
- Highlight safety and clinical assessments

**Minute 3: Human-in-the-Loop**
- Show interrupt at human approval checkpoint
- Demonstrate "Approve Protocol" flow
- Show "Request Revision" with feedback
- Watch agents rework the draft

**Minute 4: MCP Integration**
- Show VS Code with Claude Code extension
- Execute: "Create a CBT protocol for managing anxiety"
- Show tool being called
- Display returned protocol

**Minute 5: Code Walkthrough**
- Open `backend/models/state.py` - show ProtocolState structure
- Open `backend/graph/workflow.py` - show StateGraph with interrupt_before
- Open `backend/database/checkpointer.py` - show PostgresSaver setup
- Quick look at Supervisor routing logic

### What Makes This Implementation Strong

✅ **Architectural Ambition**: Supervisor-Worker pattern with autonomous iteration loops, not a simple chain  
✅ **Rich State**: 20+ fields in ProtocolState, structured scratchpad, version tracking  
✅ **True Persistence**: PostgreSQL checkpointing, resume from exact point after crashes  
✅ **Human-in-the-Loop**: Proper interrupt mechanism with approval/revision workflows  
✅ **MCP Standard**: Full implementation of Model Context Protocol with stdio transport  
✅ **Quality Control**: Multi-dimensional safety/clinical evaluation with scoring thresholds  
✅ **Self-Correction**: Agents loop internally based on quality scores before human review

## 🤝 Additional Resources

### Documentation Files

- **ARCHITECTURE.md**: Detailed technical architecture, agent designs, state management
- **QUICKSTART.md**: Condensed setup guide for rapid deployment
- **MCP_VSCODE_SETUP.md**: Step-by-step VS Code MCP integration
- **TESTING.md**: Comprehensive testing strategies
- **FINAL_SUBMISSION.md**: Project summary and submission checklist
- **DATABASE_SCHEMA.md**: PostgreSQL schema details (in backend/)

### Useful Commands

```bash
# Check all services
ps aux | grep -E "uvicorn|vite|python.*server.py"

# View backend logs
cd backend && tail -f *.log  # if logging to file

# Database quick check
psql -U postgres cerina_foundry -c "\dt"

# Restart backend with fresh state
cd backend
source venv/bin/activate
# Optionally drop and recreate DB
psql -U postgres -c "DROP DATABASE IF EXISTS cerina_foundry;"
psql -U postgres -c "CREATE DATABASE cerina_foundry;"
python -c "from database.checkpointer import init_database; init_database()"
uvicorn main:app --reload

# Build frontend for production
cd frontend
npm run build
# Serve build: npm run preview
```

### Environment Variables Reference

**Backend (.env):**
```bash
# Required
OPENAI_API_KEY=sk-proj-...        # OpenAI API key from platform.openai.com

# Database (default PostgreSQL connection)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cerina_foundry

# API Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
HOST=0.0.0.0
PORT=8000

# Optional (for debugging) - not currently used but available
LOG_LEVEL=info
DEBUG=false
```

**Note:** A `.env.example` file is provided in both the project root and `backend/` directory. The backend one is used by the application.

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: langgraph` | Activate venv: `source backend/venv/bin/activate` |
| `connection to server ... failed` | Start PostgreSQL: `brew services start postgresql@14` |
| `401 Unauthorized` (OpenAI) | Check OPENAI_API_KEY in .env, regenerate if expired |
| Frontend shows old data | Hard refresh: Cmd+Shift+R or clear browser cache |
| Infinite agent loop | Check Supervisor logic, ensure needs_revision is checked first |
| MCP server not found in VS Code | Reload VS Code window: Cmd+Shift+P → "Reload Window" |

## 📄 License & Acknowledgments

**License:** Proprietary - Cerina Health Technical Assessment Project

**Technologies Used:**
- LangGraph by LangChain - Multi-agent orchestration framework
- OpenAI GPT-4 - LLM for agent reasoning
- FastAPI - Modern Python web framework
- React - UI library
- PostgreSQL - Relational database
- Model Context Protocol (MCP) - AI interoperability standard

**Built for:** Cerina Health "Agentic Architect Sprint"  
**Timeline:** 5 days  
**Completion Date:** December 12, 2025

## 🙋 Support & Contact

This is a technical assessment project. For questions about the implementation:

1. **Check Documentation**: See ARCHITECTURE.md, QUICKSTART.md, or inline code comments
2. **Review Logs**: Check terminal output for backend/frontend errors
3. **Database State**: Query checkpoints table to see workflow state
4. **Code Comments**: All agent files have detailed docstrings

**Project Structure Philosophy:**
- Backend: Pure business logic, no UI concerns
- Frontend: Thin client, polls backend for state
- MCP: Reuses backend graph, different transport layer
- Database: Single source of truth for state

## 🎓 Learning Outcomes

This project demonstrates:

1. **Multi-Agent System Design**: Supervisor-Worker pattern with autonomous loops
2. **State Management**: Rich shared state ("blackboard" pattern)
3. **LangGraph Mastery**: StateGraph, checkpointing, interrupts, routing
4. **Human-AI Collaboration**: True human-in-the-loop with feedback cycles
5. **Protocol Integration**: MCP standard implementation
6. **Full-Stack Development**: Python backend + React frontend + MCP server
7. **Database Design**: Event sourcing with checkpoints
8. **Production Readiness**: Error handling, logging, persistence

---

**Ready to Deploy?** Follow the deployment guide above, run the tests, and you'll have a production-grade multi-agent CBT protocol generation system running in under 30 minutes! 🚀
