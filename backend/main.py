from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uuid
import logging

from backend.agents.pipeline import LucidePipeline
from backend.config import settings

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LUCIDE API",
    description="Assistant intelligent d'analyse football",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, LucidePipeline] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    entities: Dict[str, Any]
    tools: List[str]


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_model: str


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "LUCIDE API",
        "version": "2.0.0",
        "description": "Assistant football propulse par DeepSeek function calling",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    return HealthResponse(
        status="ok",
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.DEEPSEEK_MODEL if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_MODEL,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        if session_id not in sessions:
            logger.info(f"Creating new session: {session_id}")
            sessions[session_id] = LucidePipeline(session_id=session_id)

        pipeline = sessions[session_id]
        logger.info(f"Processing message for session {session_id}: {request.message[:120]}...")
        result = await pipeline.process(request.message)

        intent_obj = result["intent"]
        tool_names = [tool.name for tool in result["tool_results"]]

        return ChatResponse(
            response=result["answer"],
            session_id=session_id,
            intent=intent_obj.intent,
            entities=intent_obj.entities,
            tools=tool_names,
        )

    except Exception as exc:
        logger.error(f"Error in chat endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    if session_id in sessions:
        await sessions[session_id].close()
        del sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.on_event("startup")
async def startup_event():
    logger.info("LUCIDE API starting up...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("LUCIDE API shutting down...")
    for _, pipeline in sessions.items():
        await pipeline.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
