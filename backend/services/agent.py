"""The AI agent: Gemini decides which MCP tools to call, our code runs them, until there is an answer."""
import os
import sys
import httpx
from datetime import date
from pathlib import Path

from google.genai import errors as genai_errors, types

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from schemas import ChatResponse, ChatTurn, ToolStep
from services.receipts import MODEL, client   # reuse the same Gemini client (with retries)

BACKEND_DIR = Path(__file__).resolve().parent.parent
MAX_STEPS = 8   # safety limit: stop a confused agent from looping forever

SYSTEM_PROMPT = """You are the assistant inside a personal expense tracker. Today is {today}.
You help the user understand and manage their own spending, using the tools provided.

Rules:
- Every amount, total and comparison must come from tool results. Never estimate or invent numbers.
- For questions about a period ("this month", "last month", "in October"), work out the exact
  start_date and end_date yourself from today's date, then call query_expenses.
- Never call save_expense or set_budget unless the user has clearly asked for it or confirmed it.
  Before saving an expense, call check_duplicate; if it finds a match, ask the user first.
- If information is missing or a tool fails, say so plainly or ask the user. Do not guess.
- You can only see this user's data. If asked about other people's data, explain that you can't.
- Write plain text for a chat window: no Markdown symbols like ** or #. Simple lists starting with "- " are fine.
- Keep answers short and friendly. Show money as rupees, like Rs 1,227.00."""


def _gemini_tools(mcp_tools) -> types.Tool:
    """Turn the MCP server's tool list into the format Gemini understands."""
    return types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters_json_schema=tool.inputSchema,   # the inputs FastMCP built from the Python types
        )
        for tool in mcp_tools
    ])


async def run_agent(token: str, message: str, history: list[ChatTurn]) -> ChatResponse:
    # Start the MCP server AS this user: their token goes in the environment, never to the AI
    server = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "EXPENSE_USER_TOKEN": token},
    )
    ai_error = None
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                return await _agent_loop(session, message, history)
            except (genai_errors.APIError, httpx.TimeoutException) as e:

                ai_error = e   # don't raise it in here: the MCP connection would wrap it in an "ExceptionGroup"
    raise ai_error   # raised out here, it stays a plain Gemini error that routers/chat.py can catch


async def _agent_loop(session: ClientSession, message: str, history: list[ChatTurn]) -> ChatResponse:
    """Ask Gemini, run the tools it asks for, and repeat until it answers (at most MAX_STEPS rounds)."""
    tools = (await session.list_tools()).tools
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT.format(today=date.today().isoformat()),
        tools=[_gemini_tools(tools)],
    )

    # The conversation so far, then the new question
    contents = [
        types.Content(role=turn.role, parts=[types.Part.from_text(text=turn.text)])
        for turn in history
    ]
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

    steps: list[ToolStep] = []
    for _ in range(MAX_STEPS):
        response = await client.aio.models.generate_content(
            model=MODEL, contents=contents, config=config
        )
        contents.append(response.candidates[0].content)   # remember what Gemini said

        calls = response.function_calls
        if not calls:                                     # no tool requested -> final answer
            return ChatResponse(answer=response.text or "", steps=steps)

        # Gemini asked for tools: WE run them through MCP and report the results back
        results = []
        for call in calls:
            args = dict(call.args or {})
            result = await session.call_tool(call.name, args)
            text = result.content[0].text if result.content else ""
            output = {"error": text} if result.isError else {"result": text}
            results.append(types.Part.from_function_response(name=call.name, response=output))
            steps.append(ToolStep(tool=call.name, args=args, ok=not result.isError))
        contents.append(types.Content(role="user", parts=results))

    return ChatResponse(
        answer="Sorry, I couldn't finish that within my step limit. Could you ask in a simpler way?",
        steps=steps,
    )


#Start the MCP server as this user. This is the same thing test_mcp.py did, with the user's token in the environment.
#Ask the server for its tools and translate them into Gemini's format (_gemini_tools). The descriptions and input types come straight from your mcp_server.py. Nothing is written twice.
#Set up the conversation: the rules (SYSTEM_PROMPT), the earlier messages (history), and the new question.
#The loop (at most 8 rounds):
#Send everything to Gemini.
#If Gemini answers in words, return the answer. Done.
#If Gemini asks for tools, run each one through MCP, record it in steps, add the results to the conversation, and go round again.
#About the system prompt (section 6.5 of your report):
#"Today is {today}": an AI doesn't know today's date on its own. Without this, it can't work out what "last month" means.
#"Every amount must come from tool results" stops it from inventing numbers.
#"Never call save_expense … unless confirmed" keeps a human in the loop.
#async / await: the agent waits a lot, for Gemini and for the MCP server. await lets the server handle other users' requests while it waits. client.aio is the async version of the Gemini client.
