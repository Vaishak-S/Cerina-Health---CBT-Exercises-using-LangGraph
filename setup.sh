#!/bin/bash

# Quick Setup Script for Cerina Protocol Foundry
# This script automates the initial setup process

set -e  # Exit on error

echo "🏥 Cerina Protocol Foundry - Quick Setup"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi
echo "✅ Node found: $(node --version)"

# Setup Backend
echo ""
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Checking .env file..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your OPENAI_API_KEY"
    echo ""
fi

echo "Initializing databases..."
python3 init_db.py

cd ..

# Setup Frontend
echo ""
echo "📦 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

if [ ! -f ".env" ]; then
    echo "VITE_API_URL=http://localhost:8000" > .env
fi

cd ..

# Setup MCP Server
echo ""
echo "📦 Setting up MCP server..."
cd mcp-server
pip install -q -e .
cd ..

# Final instructions
echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Add your OpenAI API key to backend/.env:"
echo "   OPENAI_API_KEY=sk-your-key-here"
echo ""
echo "2. Start the system:"
echo "   ./start.sh"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Full documentation"
echo "   - ARCHITECTURE.md - System design"
echo "   - TESTING.md - Testing guide"
echo "   - LOOM_RECORDING_GUIDE.md - Video demo guide"
echo ""
echo "🎉 You're ready to go!"
