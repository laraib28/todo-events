"""Chat router for AI-powered natural language todo management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from openai import APIError, RateLimitError, APIConnectionError
from app.database import get_session
from app.dependencies import get_dev_or_current_user  # DEV-ONLY: Uses dev bypass in development mode
from app.models import User
from app.schemas import ChatRequest, ChatResponse
#from app.ai.agent import TodoAgent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_dev_or_current_user)  # DEV-ONLY: Bypasses auth in development mode
) -> ChatResponse:
    """Process a natural language message and perform task operations.

    This endpoint:
    1. Receives a natural language message from the user
    2. Loads conversation context from database
    3. Sends message to OpenAI Agent with MCP tools
    4. Executes any task operations via MCP tools
    5. Stores conversation messages in database
    6. Returns AI response with optional action metadata

    Args:
        request: ChatRequest with user message
        session: Database session
        current_user: Authenticated user from JWT

    Returns:
        ChatResponse with AI message and optional metadata

    Raises:
        HTTPException 429: OpenAI rate limit exceeded
        HTTPException 503: OpenAI API unavailable
        HTTPException 500: Internal server error
    """
    try:
        # Initialize agent
        agent = TodoAgent()

        # Process message
        response = await agent.process_message(
            session=session,
            user_id=current_user.id,
            user_message=request.message
        )

        return ChatResponse(
            message=response["message"],
            metadata=response.get("metadata")
        )

    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI API rate limit exceeded. Please try again later."
        )

    except APIConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to OpenAI API. Please try again later."
        )

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OpenAI API error: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
