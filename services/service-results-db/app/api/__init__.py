from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Results DB API",
    description="Storage and retrieval of CV analysis results",
    version="1.0.0"
)

app.include_router(router)

__all__ = ['app']
