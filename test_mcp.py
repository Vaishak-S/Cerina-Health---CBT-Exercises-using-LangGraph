#!/usr/bin/env python3
"""
Test MCP Server Directly
Run this to interact with the MCP server without needing Claude
"""
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server by calling generate_cbt_protocol"""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="/Users/vaishaks/.pyenv/versions/3.10.14/bin/python",
        args=["/Users/vaishaks/Desktop/Cerina Health Project/mcp-server/server.py"],
        env={
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cerina_foundry")
        }
    )
    
    print("🚀 Starting MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✅ MCP server connected!\n")
            
            # List available tools
            tools = await session.list_tools()
            print(f"📋 Available tools:")
            for tool in tools.tools:
                print(f"   - {tool.name}: {tool.description[:100]}...")
            print()
            
            # Call the generate_cbt_protocol tool
            print("🎯 Calling generate_cbt_protocol...")
            print("   Intent: Create a CBT exercise for social anxiety\n")
            
            result = await session.call_tool(
                "generate_cbt_protocol",
                arguments={
                    "user_intent": "Create a CBT exercise for social anxiety",
                    "user_context": "Patient struggles with social situations and public speaking"
                }
            )
            
            print("✨ Result:")
            for content in result.content:
                if content.type == "text":
                    data = json.loads(content.text)
                    print(f"   Protocol ID: {data['protocol_id']}")
                    print(f"   Status: {data['status']}")
                    print(f"\n   {data['message']}")
                    print(f"\n   🌐 View in browser: http://localhost:5173")
                    print(f"   📊 Or check: http://localhost:5174")


if __name__ == "__main__":
    print("=" * 60)
    print("  CERINA FOUNDRY MCP SERVER TEST")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(test_mcp_server())
        print("\n✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
