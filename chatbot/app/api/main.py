
import logging
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chatbot.app.core.config import get_settings
from chatbot.app.generation.service import answer_question


logger = logging.getLogger(__name__)
settings = get_settings()

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

# Temporary conversation context:
# session_id -> last known compound code
SESSION_CONTEXT: dict[str, str] = {}
SESSION_CONTEXT_LOCK = Lock()

app = FastAPI(
    title="SpaceEye Hybrid RAG Chatbot API",
    description="AI assistant for urban development projects.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question",
    )
    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    n_results: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    question: str
    answer: str
    intent: str | None = None
    compound: str | None = None
    evidence_count: int
    generation_mode: str


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SpaceEye Chatbot",
        "version": "1.0.0",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        # 1. Get the previous project for this conversation.
        last_compound = None

        if request.session_id:
            with SESSION_CONTEXT_LOCK:
                last_compound = SESSION_CONTEXT.get(request.session_id)

        # 2. Process the question using its conversation context.
        result = answer_question(
            question=request.question,
            n_results=request.n_results,
            last_compound=last_compound,
        )

        # 3. Save the latest detected project for this conversation.
        if request.session_id and result.get("compound"):
            with SESSION_CONTEXT_LOCK:
                SESSION_CONTEXT[request.session_id] = result["compound"]

        return ChatResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Chat request failed.")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing the question.",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
    )
