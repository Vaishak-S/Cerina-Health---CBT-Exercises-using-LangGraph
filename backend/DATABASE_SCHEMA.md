# PostgreSQL Database Schema

This document describes the required PostgreSQL database schema for the Cerina Protocol Foundry.

## Database Connection

**Connection String Format**:
```
postgresql://username:password@host:port/database_name
```

**Example**:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cerina_foundry
```

---

## Required Tables

### 1. `checkpoint` (Created by LangGraph)

**Purpose**: Stores workflow state snapshots for crash recovery and resume capability.

**Auto-created by**: `PostgresSaver.from_conn_string()`

**Schema**:
```sql
CREATE TABLE checkpoint (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE INDEX idx_checkpoint_thread_id ON checkpoint(thread_id);
CREATE INDEX idx_checkpoint_parent_id ON checkpoint(parent_checkpoint_id);
```

**Columns**:
- `thread_id`: Unique identifier for workflow instance (protocol_id)
- `checkpoint_ns`: Namespace for checkpoint (default: '')
- `checkpoint_id`: Unique checkpoint identifier (timestamp-based)
- `parent_checkpoint_id`: Reference to previous checkpoint
- `type`: Checkpoint type
- `checkpoint`: JSONB containing full workflow state
- `metadata`: JSONB containing checkpoint metadata

---

### 2. `protocol_history` (Created by SQLAlchemy)

**Purpose**: Stores all protocol generation requests and final results.

**Auto-created by**: `init_history_db()` in `database/history.py`

**Schema**:
```sql
CREATE TABLE protocol_history (
    id VARCHAR PRIMARY KEY,
    user_intent TEXT NOT NULL,
    user_context TEXT,
    final_protocol TEXT,
    iteration_count INTEGER DEFAULT 0,
    human_approved BOOLEAN DEFAULT FALSE,
    human_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    state_snapshot JSONB
);

CREATE INDEX idx_protocol_created_at ON protocol_history(created_at DESC);
CREATE INDEX idx_protocol_approved ON protocol_history(human_approved);
```

**Columns**:
- `id`: UUID for protocol request
- `user_intent`: User's therapeutic goal
- `user_context`: Additional patient context
- `final_protocol`: Approved CBT exercise text
- `iteration_count`: Number of agent iterations
- `human_approved`: Whether human approved
- `human_feedback`: Human's feedback comments
- `created_at`: Request timestamp
- `completed_at`: Completion timestamp
- `state_snapshot`: JSONB of final state

---

### 3. `agent_interactions` (Created by SQLAlchemy)

**Purpose**: Logs all agent activities and scratchpad entries for audit trail.

**Auto-created by**: `init_history_db()` in `database/history.py`

**Schema**:
```sql
CREATE TABLE agent_interactions (
    id SERIAL PRIMARY KEY,
    protocol_id VARCHAR NOT NULL,
    agent_role VARCHAR NOT NULL,
    iteration INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_protocol_id ON agent_interactions(protocol_id);
CREATE INDEX idx_agent_timestamp ON agent_interactions(timestamp DESC);
CREATE INDEX idx_agent_role ON agent_interactions(agent_role);
```

**Columns**:
- `id`: Auto-increment primary key
- `protocol_id`: Foreign key to protocol_history
- `agent_role`: Agent name (drafter, safety_guardian, clinical_critic, supervisor)
- `iteration`: Iteration number
- `content`: Agent's scratchpad message
- `timestamp`: Entry timestamp

---

### 4. `safety_logs` (Created by SQLAlchemy)

**Purpose**: Tracks all safety assessments for compliance and auditing.

**Auto-created by**: `init_history_db()` in `database/history.py`

**Schema**:
```sql
CREATE TABLE safety_logs (
    id SERIAL PRIMARY KEY,
    protocol_id VARCHAR NOT NULL,
    safety_level VARCHAR NOT NULL,
    concerns JSONB,
    recommendations JSONB,
    flagged_lines JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_safety_protocol_id ON safety_logs(protocol_id);
CREATE INDEX idx_safety_level ON safety_logs(safety_level);
CREATE INDEX idx_safety_timestamp ON safety_logs(timestamp DESC);
```

**Columns**:
- `id`: Auto-increment primary key
- `protocol_id`: Foreign key to protocol_history
- `safety_level`: 'safe', 'needs_review', or 'unsafe'
- `concerns`: JSONB array of safety concerns
- `recommendations`: JSONB array of recommendations
- `flagged_lines`: JSONB array of line numbers with issues
- `timestamp`: Assessment timestamp

---

## Setup Instructions

### 1. Install PostgreSQL

**macOS**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows**:
Download from https://www.postgresql.org/download/windows/

---

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE cerina_foundry;

# Create user (optional)
CREATE USER cerina_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE cerina_foundry TO cerina_user;

# Exit
\q
```

---

### 3. Configure Environment

Update `backend/.env`:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cerina_foundry
```

---

### 4. Initialize Tables

```bash
cd backend
source venv/bin/activate
python3 init_db.py
```

This will:
1. Create `checkpoint` table (via LangGraph's PostgresSaver)
2. Create `protocol_history`, `agent_interactions`, `safety_logs` (via SQLAlchemy)

---

## Verifying Setup

```bash
# Connect to database
psql -U postgres -d cerina_foundry

# List tables
\dt

# Expected output:
# checkpoint
# protocol_history
# agent_interactions
# safety_logs

# Check checkpoint table structure
\d checkpoint

# Check protocol_history table
\d protocol_history

# Exit
\q
```

---

## Table Relationships

```
protocol_history (1) ─────┬──── (N) agent_interactions
                          │
                          └──── (N) safety_logs

checkpoint (independent, keyed by thread_id which matches protocol_history.id)
```

---

## JSONB Column Details

### `checkpoint.checkpoint` (JSONB)
Contains complete `ProtocolState`:
```json
{
  "user_intent": "string",
  "current_draft": "string",
  "draft_versions": [...],
  "scratchpad": [...],
  "safety_assessment": {...},
  "clinical_assessment": {...},
  "iteration_count": 0,
  "requires_human_approval": false,
  ...
}
```

### `safety_logs.concerns` (JSONB)
```json
["Concern 1", "Concern 2", ...]
```

### `safety_logs.recommendations` (JSONB)
```json
["Recommendation 1", "Recommendation 2", ...]
```

---

## Performance Considerations

### Recommended Indexes (already included above)

1. **checkpoint**: `thread_id`, `parent_checkpoint_id`
2. **protocol_history**: `created_at DESC`, `human_approved`
3. **agent_interactions**: `protocol_id`, `timestamp DESC`, `agent_role`
4. **safety_logs**: `protocol_id`, `safety_level`, `timestamp DESC`

### JSONB Indexing (Optional for Large Scale)

```sql
-- Index on specific JSONB fields if querying frequently
CREATE INDEX idx_checkpoint_state ON checkpoint USING GIN (checkpoint);
CREATE INDEX idx_safety_concerns ON safety_logs USING GIN (concerns);
```

---

## Backup & Maintenance

### Backup
```bash
pg_dump -U postgres cerina_foundry > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
psql -U postgres cerina_foundry < backup_20251210.sql
```

### Vacuum (maintenance)
```sql
VACUUM ANALYZE checkpoint;
VACUUM ANALYZE protocol_history;
```

---

## Connection Pool Settings

For production, configure in `backend/database/checkpointer.py`:

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Additional connections if needed
    pool_pre_ping=True,    # Verify connections before using
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

---

## Migration Notes

If migrating from SQLite:

1. Export SQLite data:
```bash
sqlite3 cerina_foundry.db .dump > sqlite_dump.sql
```

2. Clean up SQLite-specific syntax (e.g., AUTOINCREMENT → SERIAL)

3. Import to PostgreSQL:
```bash
psql -U postgres cerina_foundry < cleaned_dump.sql
```

---

## Security Best Practices

1. **Use strong passwords**: Never use 'password' in production
2. **Limit permissions**: Create dedicated user with minimal privileges
3. **Enable SSL**: Configure PostgreSQL to require SSL connections
4. **Firewall rules**: Restrict database access to application server only
5. **Regular backups**: Automate daily backups
6. **Connection strings**: Never commit `.env` file to version control

---

## Troubleshooting

### Connection refused
```bash
# Check if PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Check port
psql -U postgres -p 5432
```

### Authentication failed
```bash
# Edit pg_hba.conf to allow local connections
# Location: /usr/local/var/postgresql@15/pg_hba.conf (macOS)
# Add: local   all   all   trust
```

### Database doesn't exist
```bash
psql -U postgres
CREATE DATABASE cerina_foundry;
```

---

## Summary

**Total Tables**: 4

1. **checkpoint** - LangGraph state snapshots (auto-created)
2. **protocol_history** - Protocol requests and results
3. **agent_interactions** - Agent activity logs
4. **safety_logs** - Safety assessment audit trail

**Key Features**:
- JSONB for flexible state storage
- Full audit trail for compliance
- Optimized indexes for performance
- Crash recovery via checkpointing
