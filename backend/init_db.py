"""
Helper script to initialize all databases
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.database.checkpointer import init_database
from backend.database.history import init_history_db

def main():
    print("🔧 Initializing Cerina Protocol Foundry databases...")
    
    print("📦 Creating LangGraph checkpointer database...")
    checkpointer = init_database()
    print("✅ Checkpointer initialized")
    
    print("📦 Creating protocol history database...")
    init_history_db()
    print("✅ History database initialized")
    
    print("\n✅ All databases initialized successfully!")
    print("You can now start the backend server with: uvicorn backend.main:app --reload")

if __name__ == "__main__":
    main()
