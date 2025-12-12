#!/usr/bin/env python3
import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def generate_protocol(user_intent, user_context=""):
    server_params = StdioServerParameters(
        command="/Users/vaishaks/.pyenv/versions/3.10.14/bin/python",
        args=["/Users/vaishaks/Desktop/Cerina Health Project/mcp-server/server.py"],
        env={
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cerina_foundry")
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "generate_cbt_protocol",
                arguments={
                    "user_intent": user_intent,
                    "user_context": user_context
                }
            )
            
            for content in result.content:
                if content.type == "text":
                    print(content.text)

if __name__ == "__main__":
    intent = sys.argv[1] if len(sys.argv) > 1 else "Create a CBT exercise"
    context = sys.argv[2] if len(sys.argv) > 2 else ""
    asyncio.run(generate_protocol(intent, context))
