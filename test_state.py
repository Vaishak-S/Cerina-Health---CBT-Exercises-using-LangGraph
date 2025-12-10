#!/usr/bin/env python3
"""Test script to debug the state retrieval issue"""
import asyncio
import sys
sys.path.insert(0, '/Users/vaishaks/Desktop/Cerina Health Project')

from backend.database.checkpointer import init_database
from backend.graph.workflow import create_graph

async def test_get_state():
    try:
        # Initialize
        checkpointer = init_database()
        graph = create_graph(checkpointer)
        
        # Test protocol ID
        protocol_id = "62599bcd-3ec9-4515-b26c-5acc405c11c2"
        config = {"configurable": {"thread_id": protocol_id}}
        
        print(f"Attempting to get state for protocol: {protocol_id}")
        state = await graph.aget_state(config)
        
        print(f"State object: {state}")
        print(f"State type: {type(state)}")
        print(f"Has values: {hasattr(state, 'values')}")
        
        if state:
            print(f"State.values: {state.values if hasattr(state, 'values') else 'NO VALUES ATTR'}")
        
    except Exception as e:
        import traceback
        print(f"\nERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv('/Users/vaishaks/Desktop/Cerina Health Project/backend/.env')
    asyncio.run(test_get_state())
