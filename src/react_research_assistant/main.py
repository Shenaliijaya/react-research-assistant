from fastapi import FastAPI

from react_research_assistant.api.tools import router as tools_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ReAct Research Assistant",
        description="Stage 1 REST API for research-agent tools.",
        version="0.1.0",
    )

    app.include_router(
        tools_router,
        prefix="/tools",
        tags=["Tools"],
    )

    return app


app = create_app()