#!/usr/bin/env python3
"""Test MCP client connection to Solana Web3 MCP Server."""

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def test():
    server_params = StdioServerParameters(
        command=str(PROJECT_ROOT / ".venv" / "bin" / "web3-mcp"),
        args=[],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCP Server connected successfully!")

            # List tools
            tools = await session.list_tools()
            print(f"🛠️  Found {len(tools.tools)} tools:")
            for tool in tools.tools[:10]:
                print(f"   - {tool.name}: {tool.description[:60]}...")
            if len(tools.tools) > 10:
                print(f"   ... and {len(tools.tools) - 10} more")


if __name__ == "__main__":
    asyncio.run(test())
