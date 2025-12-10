#!/bin/bash

# Startup script for Cerina Protocol Foundry
echo "🏥 Starting Cerina Protocol Foundry..."

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend && python3 -m venv venv && cd ..
fi

# Activate virtual environment and start backend
echo "Starting backend server..."
cd backend
source venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend development server..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Cerina Protocol Foundry is running!"
echo ""
echo "📍 Backend API: http://localhost:8000"
echo "📍 Frontend UI: http://localhost:5173"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
