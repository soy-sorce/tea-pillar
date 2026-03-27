"""FastAPI application entrypoint for the Cloud Run model service."""

from fastapi import FastAPI

from .routers import analyze_reward, health, predict, root


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="nekkoflix model service",
        version="0.3.0",
        description="Cloud Run model service for cat feature extraction and reward analysis.",
    )
    app.include_router(root.router)
    app.include_router(health.router)
    app.include_router(predict.router)
    app.include_router(analyze_reward.router)
    return app


app = create_app()
