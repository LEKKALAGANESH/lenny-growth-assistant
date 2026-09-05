from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables are created
    init_db()
    yield
    # Shutdown: Cleanup if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack AI Conversational Intelligence Platform grounded in Lenny's Podcast Transcripts.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware (configured for Next.js development and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "operational",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
