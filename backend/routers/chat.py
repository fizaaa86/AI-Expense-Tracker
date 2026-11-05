import httpx
from fastapi import APIRouter, Depends, HTTPException
from google.genai import errors as genai_errors

from auth import CurrentUser, get_current_user
from schemas import ChatRequest, ChatResponse
from services import agent

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(data: ChatRequest, user: CurrentUser = Depends(get_current_user)):
    """Ask the AI agent about your spending in plain English."""
    try:
        return await agent.run_agent(user.token, data.message, data.history)
    except genai_errors.APIError as e:
        if e.code == 429:   # Google's free usage limit
            raise HTTPException(status_code=429, detail="The AI has reached its free usage limit. Please try again later.")
        raise HTTPException(status_code=502, detail=f"The AI service failed: {e}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="The AI took too long to answer. Please try again in a minute.")


#This is a small "waiter". It checks the login, passes the question to the agent, and turns a Gemini failure into a clear 502. Notice async def, needed because it awaits the agent
