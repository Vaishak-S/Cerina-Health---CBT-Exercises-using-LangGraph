# 🚀 Quick Start Guide

Get the Cerina Protocol Foundry up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key

## Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup.sh

# Add your API key
nano backend/.env
# Set: OPENAI_API_KEY=sk-your-key-here

# Start the system
./start.sh
```

Done! Go to http://localhost:5173

## Option 2: Manual Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env and add your API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
echo "DATABASE_URL=sqlite:///./cerina_foundry.db" >> .env

# Initialize database
python3 init_db.py

# Start server
uvicorn main:app --reload
```

### Frontend (in new terminal)

```bash
cd frontend
npm install
npm run dev
```

### Access

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## First Test

1. Open http://localhost:5173
2. Enter intent: `"Create a breathing exercise for anxiety"`
3. Click "Generate Protocol"
4. Watch agents collaborate
5. Approve when prompted

## MCP Setup (Optional)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-server/server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

Restart Claude Desktop and ask:
```
"Use the Cerina Foundry to create a sleep hygiene protocol"
```

## Troubleshooting

**Port already in use**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Database errors**:
```bash
# Reset database
rm backend/cerina_foundry.db
python3 backend/init_db.py
```

**Missing dependencies**:
```bash
# Reinstall
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

## Documentation

- **README.md** - Complete documentation
- **ARCHITECTURE.md** - System design
- **TESTING.md** - Testing guide
- **IMPLEMENTATION_SUMMARY.md** - Project overview
- **LOOM_RECORDING_GUIDE.md** - Video demo checklist

## Need Help?

Check the comprehensive guides in the repository root directory.
