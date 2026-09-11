from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI

from react_research_assistant.api.calculator import router as calculator_router
from react_research_assistant.api.retrieval import router as retrieval_router
from react_research_assistant.api.tools import router as tools_router
from react_research_assistant.api.agent import router as agent_router
from react_research_assistant.api.ingest import router as ingest_router
from react_research_assistant.api.health import router as health_router
from react_research_assistant.api.info import router as info_router
from react_research_assistant.services.retrieval import initialize_retrieval


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared application resources before serving requests."""

    initialize_retrieval()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ReAct Research Assistant",
        description="Stage 1 REST API for research-agent tools.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(
        tools_router,
        prefix="/tools",
        tags=["Tools"],
    )

    app.include_router(
        calculator_router,
        prefix="/tools",
        tags=["Tools"],
    )

    app.include_router(
        retrieval_router,
        prefix="/tools",
        tags=["Tools"],
    )

    app.include_router(
        agent_router,
        prefix="/agent",
        tags=["Agent"],
    )

    app.include_router(
        ingest_router,
        prefix="/ingest",
        tags=["Ingestion"],
    )

    app.include_router(
        health_router,
        tags=["Health"],
    )

    app.include_router(
        info_router,
        prefix="/agent",
        tags=["Agent"],
    )

    return app


app = create_app()