# Cerina Protocol Foundry - Architecture Diagram

## System Architecture Overview

```mermaid
graph TB
    %% Styling
    classDef frontend fill:#61dafb,stroke:#333,stroke-width:2px,color:#000
    classDef backend fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff
    classDef agent fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#000
    classDef database fill:#95e1d3,stroke:#333,stroke-width:2px,color:#000
    classDef mcp fill:#ffd93d,stroke:#333,stroke-width:2px,color:#000
    classDef external fill:#a8dadc,stroke:#333,stroke-width:2px,color:#000

    %% User Interfaces
    User[👤 Human User]:::external
    MCPClient[🖥️ MCP Client<br/>Claude Desktop/VS Code]:::external
    
    %% Frontend Layer
    ReactUI[⚛️ React Frontend<br/>localhost:5173<br/>- Agent Visualization<br/>- Real-time Updates<br/>- Approve/Revision UI]:::frontend
    
    %% API Layer
    FastAPI[🚀 FastAPI Server<br/>localhost:8000<br/>- POST /api/protocols<br/>- GET /api/protocols/:id/state<br/>- POST /api/protocols/:id/feedback<br/>- WebSocket /ws/:id]:::backend
    
    %% MCP Layer
    MCPServer[📡 MCP Server<br/>stdio transport<br/>- generate_cbt_protocol tool<br/>- Async → Sync Bridge]:::mcp
    
    %% LangGraph Workflow
    Workflow[🔄 LangGraph StateGraph<br/>- Supervisor-Worker Pattern<br/>- interrupt_before: human_approval<br/>- Checkpointing Enabled]:::backend
    
    %% Agents
    Supervisor[🎯 Supervisor Agent<br/>- Route decisions<br/>- Check needs_revision<br/>- Evaluate draft quality<br/>- Decide when ready]:::agent
    
    Drafter[✍️ Drafter Agent<br/>- Generate CBT drafts<br/>- Incorporate feedback<br/>- Clear revision flags<br/>- Iteration tracking]:::agent
    
    Safety[🛡️ Safety Guardian<br/>- Check harm risks<br/>- Flag dangerous content<br/>- Medical advice detection<br/>- Safety scoring]:::agent
    
    Clinical[⚕️ Clinical Critic<br/>- Empathy score<br/>- Structure evaluation<br/>- Clinical appropriateness<br/>- Quality feedback]:::agent
    
    HumanApproval[⏸️ Human Approval Node<br/>- Interrupt Point<br/>- Wait for feedback<br/>- Resume on approval]:::agent
    
    %% State Management
    SharedState[📋 Shared State<br/>ProtocolState<br/>- user_intent & context<br/>- current_draft & versions<br/>- scratchpad notes<br/>- safety_assessment<br/>- clinical_assessment<br/>- needs_revision flag<br/>- human_approved flag<br/>- iteration_count<br/>- messages]:::backend
    
    %% Database Layer
    Postgres[(🗄️ PostgreSQL<br/>cerina_foundry<br/>- checkpoints table<br/>- checkpoint_writes table<br/>- State persistence<br/>- Crash recovery)]:::database
    
    Checkpointer[💾 PostgresSaver<br/>Sync Checkpointer<br/>- Save after each node<br/>- Resume from interrupts<br/>- Thread-based isolation]:::database
    
    %% External Services
    OpenAI[🤖 OpenAI GPT-4<br/>- LLM for all agents<br/>- Structured outputs<br/>- JSON responses]:::external
    
    %% User Flow - React UI Path
    User -->|1. Submit Intent| ReactUI
    ReactUI -->|2. HTTP POST| FastAPI
    FastAPI -->|3. Invoke Graph| Workflow
    
    %% MCP Flow - Machine-to-Machine Path
    MCPClient -->|1. Call Tool| MCPServer
    MCPServer -->|2. Invoke Graph| Workflow
    
    %% Workflow Orchestration
    Workflow -->|Load/Save State| SharedState
    SharedState <-->|Persist| Checkpointer
    Checkpointer <-->|SQL Transactions| Postgres
    
    %% Agent Collaboration Flow
    Workflow -->|Start| Supervisor
    Supervisor -->|No Draft| Drafter
    Supervisor -->|Need Safety Check| Safety
    Supervisor -->|Need Quality Check| Clinical
    Supervisor -->|Ready for Human| HumanApproval
    
    Drafter -->|Draft Ready| Supervisor
    Safety -->|Assessment Done| Supervisor
    Clinical -->|Scores Computed| Supervisor
    
    %% All agents access shared state
    Supervisor <-->|Read/Write| SharedState
    Drafter <-->|Read/Write| SharedState
    Safety <-->|Read/Write| SharedState
    Clinical <-->|Read/Write| SharedState
    HumanApproval <-->|Read/Write| SharedState
    
    %% LLM Integration
    Drafter -->|Generate Text| OpenAI
    Safety -->|Analyze Safety| OpenAI
    Clinical -->|Evaluate Quality| OpenAI
    
    %% Human-in-the-Loop
    HumanApproval -->|4. Interrupt & Save| Checkpointer
    FastAPI -->|5. Poll State| Checkpointer
    ReactUI -->|6. Display Draft| User
    User -->|7a. Approve| ReactUI
    User -->|7b. Request Revision| ReactUI
    ReactUI -->|8. Submit Feedback| FastAPI
    FastAPI -->|9. Update State| Checkpointer
    FastAPI -->|10. Resume Graph| Workflow
    Workflow -->|Revision Needed| Drafter
    Workflow -->|Approved| FastAPI
    
    %% Response Flow
    FastAPI -->|11. Return Result| ReactUI
    MCPServer -->|Return Protocol| MCPClient
    ReactUI -->|12. Show Final| User
```

## Detailed Flow Descriptions

### 1. React UI Flow (Human-in-the-Loop)

```mermaid
sequenceDiagram
    participant User
    participant React
    participant FastAPI
    participant LangGraph
    participant Supervisor
    participant Drafter
    participant Safety
    participant Clinical
    participant DB
    participant OpenAI

    User->>React: Enter CBT intent
    React->>FastAPI: POST /api/protocols
    FastAPI->>LangGraph: workflow.invoke()
    
    LangGraph->>Supervisor: Route decision
    Supervisor->>Drafter: Generate draft
    Drafter->>OpenAI: Generate CBT content
    OpenAI-->>Drafter: Return text
    Drafter->>DB: Save state
    
    Drafter->>Supervisor: Draft ready
    Supervisor->>Safety: Evaluate safety
    Safety->>OpenAI: Analyze risks
    OpenAI-->>Safety: Safety assessment
    Safety->>DB: Save assessment
    
    Safety->>Supervisor: Safety OK
    Supervisor->>Clinical: Evaluate quality
    Clinical->>OpenAI: Score empathy/structure
    OpenAI-->>Clinical: Quality scores
    Clinical->>DB: Save scores
    
    Clinical->>Supervisor: Scores: 9.2/10
    Supervisor->>LangGraph: Route to human_approval
    LangGraph->>DB: INTERRUPT & checkpoint
    
    loop Polling every 2 seconds
        React->>FastAPI: GET /api/protocols/:id/state
        FastAPI->>DB: Fetch checkpoint
        DB-->>React: Current state
    end
    
    React->>User: Show draft + agents' scratchpad
    
    alt User Approves
        User->>React: Click "Approve Protocol"
        React->>FastAPI: POST feedback {approved: true}
        FastAPI->>DB: Set human_approved=true
        FastAPI->>LangGraph: Resume from checkpoint
        LangGraph->>DB: Save final_protocol
        LangGraph-->>FastAPI: Complete
        FastAPI-->>React: Success
        React->>User: Show completed protocol
    else User Requests Revision
        User->>React: Enter feedback + Click "Request Revision"
        React->>FastAPI: POST feedback {revision: "feedback text"}
        FastAPI->>DB: Set needs_revision=true
        FastAPI->>LangGraph: Resume from checkpoint
        LangGraph->>Supervisor: Check needs_revision
        Supervisor->>Drafter: Revise with feedback
        Drafter->>OpenAI: Generate improved draft
        Drafter->>DB: Save new version
        Note over LangGraph,DB: Loop continues until approved
    end
```

### 2. MCP Server Flow (Machine-to-Machine)

```mermaid
sequenceDiagram
    participant Claude as Claude Desktop/VS Code
    participant MCP as MCP Server (stdio)
    participant Thread as ThreadPoolExecutor
    participant LangGraph
    participant DB as PostgreSQL
    participant Agents

    Claude->>MCP: "Create CBT protocol for anxiety"
    MCP->>MCP: Receive via stdio
    MCP->>MCP: Parse tool call
    
    Note over MCP,Thread: Async→Sync Bridge
    MCP->>Thread: executor.submit(run_sync_graph)
    Thread->>LangGraph: workflow.invoke() [SYNC]
    
    LangGraph->>Agents: Execute full workflow
    Agents->>DB: Checkpoint each step
    
    Note over LangGraph,Agents: No human interrupt<br/>Auto-approve if quality ≥8.0
    
    Agents-->>LangGraph: Complete
    LangGraph->>DB: Save final state
    LangGraph-->>Thread: Return protocol
    Thread-->>MCP: Future.result()
    MCP->>MCP: Format as markdown
    MCP-->>Claude: Return protocol text
    
    Claude->>Claude: Display to user
```

### 3. Agent Decision Flow

```mermaid
graph TD
    Start([New Protocol Request])
    Start --> Supervisor1[Supervisor: Check State]
    
    Supervisor1 --> CheckRevision{needs_revision<br/>flag set?}
    CheckRevision -->|Yes| Drafter1[Drafter: Incorporate<br/>human feedback]
    CheckRevision -->|No| CheckDraft{Has draft?}
    
    CheckDraft -->|No| Drafter2[Drafter: Create<br/>initial draft]
    CheckDraft -->|Yes| CheckSafety{Safety<br/>assessed?}
    
    Drafter1 --> Supervisor2[Supervisor]
    Drafter2 --> Supervisor2
    
    CheckSafety -->|No| Safety1[Safety Guardian:<br/>Analyze risks]
    CheckSafety -->|Yes| CheckClinical{Clinical<br/>assessed?}
    
    Safety1 --> Supervisor3[Supervisor]
    
    CheckClinical -->|No| Clinical1[Clinical Critic:<br/>Score quality]
    CheckClinical -->|Yes| CheckQuality{Quality ≥ 8.0?}
    
    Clinical1 --> Supervisor4[Supervisor]
    
    CheckQuality -->|No| Drafter3[Drafter: Improve<br/>based on feedback]
    CheckQuality -->|Yes| HumanNode[Human Approval Node:<br/>INTERRUPT]
    
    Drafter3 --> Supervisor5[Supervisor]
    Supervisor2 --> CheckSafety
    Supervisor3 --> CheckClinical
    Supervisor4 --> CheckQuality
    Supervisor5 --> CheckSafety
    
    HumanNode --> WaitDB[(Save to DB<br/>Wait for human)]
    WaitDB --> HumanDecision{Human Decision}
    
    HumanDecision -->|Approve| Complete([Save Final Protocol])
    HumanDecision -->|Revise| SetFlag[Set needs_revision=true<br/>Store feedback]
    SetFlag --> Supervisor6[Supervisor]
    Supervisor6 --> CheckRevision
    
    style Start fill:#90EE90
    style Complete fill:#FFD700
    style HumanNode fill:#FF6B6B
    style WaitDB fill:#87CEEB
```

## Key Architectural Decisions

### 1. **Supervisor-Worker Pattern**
- **Supervisor Agent**: Central orchestrator that makes routing decisions
- **Worker Agents**: Specialized agents (Drafter, Safety, Clinical) that execute tasks
- **Advantages**: Clear separation of concerns, flexible routing, easy to add new agents

### 2. **Shared State (Blackboard Pattern)**
- All agents read/write to a centralized `ProtocolState`
- Enables rich communication via scratchpad notes
- Tracks versions, iterations, and metadata
- Immutable history through checkpoint system

### 3. **Interrupt-Based Human-in-the-Loop**
- Graph pauses at `interrupt_before=["human_approval"]`
- State persisted to PostgreSQL checkpoint
- Frontend polls for state updates
- Resume execution after human feedback

### 4. **Dual Interface Architecture**
- **React UI**: Visual, human-centric, real-time agent monitoring
- **MCP Server**: Programmatic, machine-centric, tool-based access
- Both use the same LangGraph workflow core

### 5. **Persistence Strategy**
- PostgreSQL with sync `PostgresSaver`
- Checkpoints saved after every agent execution
- Crash-recovery capable
- Thread-based isolation via `thread_id`

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 19.2 + TypeScript | User interface with real-time updates |
| API | FastAPI 0.110+ | REST endpoints, WebSocket support |
| Workflow | LangGraph 0.2+ | Agent orchestration, state management |
| Agents | LangChain + OpenAI | LLM-powered reasoning and generation |
| MCP | mcp-python 0.9+ | Model Context Protocol server |
| Database | PostgreSQL | Persistent checkpointing and history |
| Dev Server | Vite 7.2 | Fast frontend development |
| Server | Uvicorn | ASGI server for FastAPI |

## State Flow Example

```python
# Initial State
{
    "user_intent": "Create exposure hierarchy for agoraphobia",
    "current_draft": None,
    "iteration_count": 0,
    "needs_revision": False
}

# After Drafter (Iteration 1)
{
    "current_draft": "Step 1: Practice looking at photos...",
    "draft_versions": [{"version": 1, "text": "..."}],
    "scratchpad": "Drafter: Created initial 5-step hierarchy",
    "iteration_count": 1
}

# After Safety Guardian
{
    "safety_assessment": {
        "level": "safe",
        "concerns": [],
        "recommendations": []
    },
    "scratchpad": "Drafter: Created initial 5-step hierarchy\nSafety: No risks detected"
}

# After Clinical Critic
{
    "clinical_assessment": {
        "empathy_score": 9.0,
        "structure_score": 9.0,
        "clinical_appropriateness": 9.5,
        "feedback": "Excellent progression, empathetic tone"
    },
    "scratchpad": "...\nClinical: High quality, approved for human review"
}

# At Human Approval (INTERRUPTED)
{
    "requires_human_approval": True,
    "human_approved": None,
    # Graph paused, state saved to PostgreSQL
}

# After Human Revision Request
{
    "needs_revision": True,
    "revision_reason": "Add more detail to step 3",
    "human_approved": False,
    "iteration_count": 2  # Will increment on next Drafter run
}

# Final State (After Approval)
{
    "human_approved": True,
    "completed": True,
    "final_protocol": "...",
    "iteration_count": 3
}
```

## Rendering Instructions

To generate the architecture diagram image:

### Option 1: Using Mermaid Live Editor (Recommended)
1. Visit https://mermaid.live/
2. Copy the first mermaid diagram from this file
3. Paste it into the editor
4. Click "Download PNG" or "Download SVG"

### Option 2: Using GitHub
1. Create a new file `architecture.md` in your repository
2. Paste the mermaid diagram code
3. GitHub will automatically render it
4. Take a screenshot

### Option 3: Using VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Open this file in VS Code
3. Use Preview (Cmd+Shift+V)
4. Right-click diagram → Copy as PNG

### Option 4: Using CLI
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.png
```

## System Metrics

- **Total Agents**: 4 (Supervisor, Drafter, Safety Guardian, Clinical Critic)
- **API Endpoints**: 4 (POST /protocols, GET /state, POST /feedback, GET /health)
- **Database Tables**: 2 (checkpoints, checkpoint_writes)
- **State Fields**: 19 (comprehensive tracking)
- **Average Iterations**: 3-5 per protocol
- **Resume Capability**: 100% (checkpoint after every node)
