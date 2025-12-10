# System Architecture Diagram

## Cerina Protocol Foundry - Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
├────────────────────────┬────────────────────────────────────────────┤
│   React Dashboard      │          MCP Client (Claude Desktop)       │
│   - Real-time UI       │          - Tool invocation                 │
│   - Human-in-Loop      │          - Auto-approve mode               │
│   - WebSocket stream   │                                            │
└───────────┬────────────┴──────────────────┬─────────────────────────┘
            │                               │
            │ HTTP/WS                       │ stdio
            ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INTERFACE LAYER                                 │
├─────────────────────────────┬───────────────────────────────────────┤
│   FastAPI Backend           │      MCP Server (mcp-python)          │
│   - REST API                │      - Tool: generate_cbt_protocol    │
│   - WebSocket handler       │      - Resource: latest protocol      │
│   - State management        │                                       │
└──────────────┬──────────────┴──────────────┬────────────────────────┘
               │                             │
               │                             │
               └─────────────┬───────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW ENGINE                         │
│                  (Supervisor-Worker Pattern)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────────────────────────────────────────────┐         │
│   │              SUPERVISOR AGENT                        │         │
│   │  - Orchestrates workflow                             │         │
│   │  - Routes to appropriate agents                      │         │
│   │  - Evaluates quality thresholds                      │         │
│   │  - Decides when to request human approval            │         │
│   └────┬─────────────────────────────────────────────┬───┘         │
│        │                                             │              │
│        ▼                                             ▼              │
│   ┌─────────────────┐                         ┌──────────────────┐ │
│   │ DRAFTER AGENT   │◄──────────────────────►│  CLINICAL CRITIC │ │
│   │ - Creates draft │                         │  - Empathy score │ │
│   │ - Revises based │                         │  - Structure     │ │
│   │   on feedback   │                         │  - Appropriateness│ │
│   └────────┬────────┘                         └────────┬─────────┘ │
│            │                                           │            │
│            │         ┌──────────────────┐             │            │
│            └────────►│ SAFETY GUARDIAN  │◄────────────┘            │
│                      │ - Risk detection │                          │
│                      │ - Content safety │                          │
│                      │ - Flagging       │                          │
│                      └──────────────────┘                          │
│                                                                      │
│   ┌──────────────────────────────────────────────────────┐         │
│   │           INTERRUPT POINT: HUMAN APPROVAL            │         │
│   │  - Workflow pauses for human review                  │         │
│   │  - State persisted to database                       │         │
│   │  - User can edit or approve                          │         │
│   └──────────────────────────────────────────────────────┘         │
│                                                                      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SHARED STATE ("BLACKBOARD")                      │
├─────────────────────────────────────────────────────────────────────┤
│  • User Intent & Context                                            │
│  • Current Draft + Version History                                  │
│  • Scratchpad (Agent-to-Agent Notes)                                │
│  • Safety Assessment (level, concerns, recommendations)             │
│  • Clinical Assessment (scores, feedback)                           │
│  • Metadata (iteration count, routing info)                         │
│  • Human Feedback (approval, edits)                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                               │
├───────────────────────────────┬─────────────────────────────────────┤
│   LangGraph Checkpointer      │   Protocol History Database         │
│   - SqliteSaver/PostgresSaver │   - SQLAlchemy ORM                  │
│   - State snapshots           │   - Protocol records                │
│   - Crash recovery            │   - Agent interactions log          │
│   - Resume from checkpoint    │   - Safety audit trail              │
└───────────────────────────────┴─────────────────────────────────────┘
```

## Workflow Flow

```
1. User Request
   ├─→ [REST API] or [MCP Tool Call]
   │
2. Initialize State
   ├─→ user_intent, user_context
   ├─→ iteration_count = 0
   │
3. SUPERVISOR: Route to first agent
   ├─→ DRAFTER
   │
4. DRAFTER: Create initial draft
   ├─→ Update current_draft
   ├─→ Log to scratchpad
   │
5. SUPERVISOR: Route to SAFETY_GUARDIAN
   │
6. SAFETY_GUARDIAN: Check safety
   ├─→ Create safety_assessment
   ├─→ Flag concerns if any
   │
7. SUPERVISOR: Route to CLINICAL_CRITIC
   │
8. CLINICAL_CRITIC: Evaluate quality
   ├─→ Create clinical_assessment
   ├─→ Score empathy, structure, appropriateness
   │
9. SUPERVISOR: Decision point
   ├─→ If quality < threshold → REVISION LOOP (back to step 3)
   ├─→ If unsafe → REVISION LOOP
   ├─→ If max_iterations → HUMAN APPROVAL
   ├─→ If all pass → HUMAN APPROVAL
   │
10. INTERRUPT: Human approval node
    ├─→ Workflow PAUSES
    ├─→ State saved to checkpoint
    ├─→ Wait for human input
    │
11. Human Reviews
    ├─→ Option A: Approve (with or without edits)
    ├─→ Option B: Request revision (back to step 3)
    │
12. If Approved
    ├─→ Save final_protocol
    ├─→ Mark completed = True
    ├─→ END
```

## Agent Communication Pattern

```
┌─────────────┐
│ Scratchpad  │ ◄─── All agents write notes here
└─────────────┘
     ▲
     │
     ├─ Drafter: "Created draft version 2"
     ├─ Safety: "No safety concerns detected"
     ├─ Critic: "Empathy score 8.5/10, structure clear"
     └─ Supervisor: "All checks passed - ready for human review"
```

## Technology Mapping

- **Agents**: LangChain ChatOpenAI with custom prompts
- **State**: TypedDict with Pydantic models
- **Workflow**: LangGraph StateGraph with conditional edges
- **Checkpointing**: LangGraph SqliteSaver/PostgresSaver
- **API**: FastAPI with async endpoints
- **Streaming**: WebSocket for real-time updates
- **MCP**: mcp-python Server with stdio transport
