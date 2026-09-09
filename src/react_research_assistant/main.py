from contextlib import asynccontextmanager

from fastapi import FastAPI

from react_research_assistant.api.calculator import router as calculator_router
from react_research_assistant.api.retrieval import router as retrieval_router
from react_research_assistant.api.tools import router as tools_router
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

    return app


app = create_app()