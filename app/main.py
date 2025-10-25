from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import search
import logging

app = FastAPI(
    title="Minerva Library Search API",
    description="Unified search across academic databases",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {
        "message": "Minerva Library Search API",
        "version": "0.1.0",
        "status": "running"
    }