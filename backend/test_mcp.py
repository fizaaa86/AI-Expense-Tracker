"""Try the MCP server the way an AI client would: start it, list its tools, call a few."""
import asyncio
import getpass
import os
import sys

import httpx
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
HERE = os.path.dirname(os.path.abspath(__file__))


def login() -> str:
    """Log in to Supabase and return an access token (same as get_token.py)."""
    response = httpx.post(
        f"{os.environ['SUPABASE_URL'].rstrip('/')}/auth/v1/token",
        params={"grant_type": "password"},
        headers={"apikey": os.environ["SUPABASE_ANON_KEY"]},
        json={"email": input("Email: "), "password": getpass.getpass("Password: ")},
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def main():
    token = login()
    server = StdioServerParameters(
        command=sys.executable,                              # the same Python (from .venv)
        args=["mcp_server.py"],
        cwd=HERE,
        env={**os.environ, "EXPENSE_USER_TOKEN": token},    # WHO the user is: set by us, not by the AI
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("\nTools the AI can see:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description.splitlines()[0]}")

            for name, args in [
                ("query_expenses", {"category": "Food"}),
                ("check_budget", {}),
                ("check_duplicate", {"merchant": "cafe sereno", "expense_date": "2026-05-14", "total": 1227}),
            ]:
                result = await session.call_tool(name, args)
                print(f"\n>>> {name}({args})")
                print(result.content[0].text)


asyncio.run(main())
