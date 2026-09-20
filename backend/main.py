from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.routers import prices
from scheduler.jobs import setup_scheduler
from contextlib import asynccontextmanager

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield


app = FastAPI(
    title="Energy Market Predictor API",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prices.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
