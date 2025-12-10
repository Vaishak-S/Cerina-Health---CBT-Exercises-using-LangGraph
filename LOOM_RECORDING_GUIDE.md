# 🎥 Loom Video Recording Checklist

**Time Limit**: 5 minutes maximum  
**Focus**: React UI, MCP demo, Code walkthrough

---

## 📝 Pre-Recording Setup

### Before You Start Recording:

- [ ] Backend running at `http://localhost:8000`
- [ ] Frontend running at `http://localhost:5173`
- [ ] Browser open to frontend
- [ ] MCP server configured in Claude Desktop
- [ ] Claude Desktop app open
- [ ] Code editor open to key files:
  - `backend/models/state.py`
  - `backend/database/checkpointer.py`
  - `backend/graph/workflow.py`
- [ ] Close unnecessary browser tabs
- [ ] Clear browser console
- [ ] Test workflow once before recording

---

## 🎬 Segment 1: React UI Demo (2 minutes)

### Script:

**[00:00 - 00:15] Introduction**
```
"Hi, I'm demonstrating the Cerina Protocol Foundry - a multi-agent system 
for autonomous CBT exercise generation. Let me show you the React dashboard 
with human-in-the-loop workflow."
```

**[00:15 - 00:30] Input Form**
- [ ] Show homepage with clean UI
- [ ] Point out "User Intent" field
- [ ] Enter: `"Create a thought record exercise for anxiety"`
- [ ] Add context: `"Patient experiencing work-related stress"`
- [ ] Click "Generate Protocol"

**[00:30 - 01:10] Agent Deliberation**
- [ ] Highlight agent scratchpad appearing in real-time
- [ ] Point out color-coded agents:
  - 🔵 Drafter (blue)
  - 🔴 Safety Guardian (red)
  - 🟣 Clinical Critic (purple)
  - 🟠 Supervisor (orange)
- [ ] Read a few agent entries aloud:
  ```
  "Notice the Drafter creates the initial exercise..."
  "Safety Guardian evaluates for safety concerns..."
  "Clinical Critic scores empathy, structure, and appropriateness..."
  "Supervisor decides whether to iterate or proceed..."
  ```
- [ ] Emphasize: "This is true multi-agent collaboration"

**[01:10 - 01:30] Assessments Display**
- [ ] Show Safety Assessment panel
  - "Level: SAFE" with green indicator
- [ ] Show Clinical Quality scores
  - Point out Empathy, Structure, Clinical scores
  - Highlight average calculation

**[01:30 - 01:50] Current Draft**
- [ ] Scroll through the generated CBT exercise
- [ ] Mention: "This is the result of multiple agent iterations"
- [ ] Show it's editable

**[01:50 - 02:00] Human-in-the-Loop Interrupt**
- [ ] Highlight "Human Review Required" panel
- [ ] Point out: "The workflow has PAUSED waiting for human approval"
- [ ] Show state is persisted to database
- [ ] Optional: Edit a line in the draft
- [ ] Type feedback: "Excellent work, approved"
- [ ] Click "✓ Approve Protocol"

**[02:00 - 02:10] Completion**
- [ ] Show "Workflow Complete" success message
- [ ] Mention: "Protocol is now saved to database with full audit trail"

---

## 🤖 Segment 2: MCP Integration Demo (1 minute)

### Script:

**[02:10 - 02:20] Setup Context**
```
"Now let's see the same system accessed via Model Context Protocol. 
I've integrated this as an MCP server that Claude Desktop can call."
```

**[02:20 - 02:30] Show Configuration**
- [ ] Briefly show Claude Desktop config file
- [ ] Point out: `"cerina-foundry"` server entry

**[02:30 - 02:45] Invoke Tool**
- [ ] Switch to Claude Desktop
- [ ] Type in chat:
  ```
  "Use the Cerina Foundry to create a progressive muscle 
  relaxation exercise for stress management"
  ```
- [ ] Hit Enter

**[02:45 - 03:00] Show Results**
- [ ] Point out tool appears in Claude's tool list
- [ ] Show Claude calling `generate_cbt_protocol`
- [ ] Highlight returned output:
  - Agent deliberation log
  - Safety assessment
  - Clinical scores
  - Final protocol
- [ ] Emphasize: "Same backend, different interface - this is the power of MCP"

---

## 💻 Segment 3: Code Walkthrough (2 minutes)

### Script:

**[03:00 - 03:15] State Definition**
- [ ] Open `backend/models/state.py`
- [ ] Scroll to `ProtocolState` TypedDict
```
"Here's our rich shared state - the 'blackboard' where agents collaborate.
Notice we have:
- Draft versions with full history
- Scratchpad for agent notes
- Safety and clinical assessments
- Iteration tracking
- Human feedback fields"
```
- [ ] Point out `Annotated[List, operator.add]` for append-only lists
- [ ] Show Pydantic models for assessments

**[03:15 - 03:35] Checkpointer Setup**
- [ ] Open `backend/database/checkpointer.py`
```
"For persistence, we use LangGraph's checkpointer.
This automatically saves state at every node.
If the server crashes, we can resume exactly where we left off."
```
- [ ] Show `SqliteSaver.from_conn_string()` line
- [ ] Point out PostgreSQL support option
- [ ] Mention: "Every workflow step is persisted"

**[03:35 - 04:45] Workflow Routing**
- [ ] Open `backend/graph/workflow.py`
- [ ] Show `create_graph()` function
```
"This is our LangGraph workflow definition.
We add nodes for each agent..."
```
- [ ] Point out nodes being added:
  ```python
  workflow.add_node("drafter", drafter)
  workflow.add_node("safety_guardian", safety_guardian)
  workflow.add_node("clinical_critic", clinical_critic)
  workflow.add_node("supervisor", supervisor)
  ```

- [ ] Show routing logic:
  ```python
  workflow.add_conditional_edges(
      "supervisor",
      should_continue,
      {...}
  )
  ```

- [ ] Highlight interrupt mechanism:
  ```python
  interrupt_before=["human_approval"]
  ```
  
```
"This interrupt_before is KEY - it pauses the workflow 
at the human_approval node, waits for human input, 
then resumes when we submit feedback."
```

**[04:45 - 05:00] Closing**
```
"So in summary:
- We have 4 autonomous agents collaborating via shared state
- All state is persisted with checkpointing
- Human-in-the-loop pauses workflow reliably
- Accessible via React UI or MCP
- Production-ready architecture

Thanks for watching!"
```

---

## 🎯 Key Points to Emphasize

Throughout the video, make sure to highlight:

1. **Not a Simple Chain** - This is true multi-agent collaboration with loops
2. **Autonomy** - Agents iterate multiple times before asking for human input
3. **State Richness** - Structured data, not just messages
4. **Persistence** - Database-backed with crash recovery
5. **Transparency** - Real-time visibility into agent reasoning
6. **MCP Integration** - Modern interoperability standard
7. **Production Quality** - Type safety, error handling, proper architecture

---

## ⚠️ Common Mistakes to Avoid

- ❌ Don't spend time on setup/installation
- ❌ Don't apologize for UI design choices
- ❌ Don't go into deep technical details (save for code section)
- ❌ Don't show errors or failed attempts
- ❌ Don't exceed 5 minutes!
- ❌ Don't forget to emphasize the architectural sophistication

---

## ✅ Success Checklist

After recording, verify video shows:

- [ ] Agent scratchpad with all 4 agents visible
- [ ] Real-time updates happening
- [ ] Safety assessment displayed
- [ ] Clinical scores displayed
- [ ] Human-in-the-loop interrupt working
- [ ] Draft being approved
- [ ] MCP tool being called in Claude
- [ ] State definition in code
- [ ] Checkpointer configuration
- [ ] Workflow routing with interrupt

---

## 🎨 Presentation Tips

- **Speak clearly and confidently**
- **Move cursor to highlight important elements**
- **Use a smooth, steady pace**
- **Smile when you speak** (yes, it affects your voice!)
- **Practice once before recording**
- **Have a backup example ready** in case one fails
- **Keep energy high throughout**

---

## 📹 Technical Recording Tips

- Use 1080p resolution
- Enable system audio if demoing sound
- Close notification popups
- Use a clean desktop background
- Maximize browser windows for visibility
- Use zoom/highlight features if available in Loom
- Test microphone before starting

---

## 🔄 If You Need to Re-Record

If something goes wrong:

1. **Don't panic** - Loom lets you trim and edit
2. **Restart cleanly** - Reset the workflow, clear browser
3. **Use a simpler example** - "Create a breathing exercise" is fast
4. **Focus on what works** - Show your best features
5. **Time management** - If running long, skip optional parts

---

## 📤 After Recording

- [ ] Watch the full video yourself
- [ ] Check audio quality
- [ ] Verify all key points covered
- [ ] Add chapters/timestamps in Loom (optional)
- [ ] Share link with appropriate permissions
- [ ] Include in submission with:
  - Code repository
  - Architecture diagram
  - This documentation

---

Good luck! You've built something impressive - now show it off! 🚀
