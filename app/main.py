from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import TripRequest, TripPlanResponse, SingleDayReplanRequest, DayPlan
from app.agents.orchestrator import MultiAgentOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TripMindAI")

app = FastAPI(
    title="TripMind AI — Multi-Agent Travel Planner",
    version=settings.VERSION,
    description="Autonomous Multi-Agent AI System for personalized, weather-adaptive travel planning."
)

# CORS middleware for versatile deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health_check():
    has_key = bool(settings.GEMINI_API_KEY)
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "gemini_configured": has_key,
        "active_agents": [
            "OrchestratorAgent",
            "DestinationResearchAgent",
            "WeatherEnvironmentalAgent",
            "ItineraryPlanningAgent",
            "BudgetOptimizerAgent",
            "CriticValidationAgent"
        ]
    }


@app.post("/api/plan", response_model=TripPlanResponse)
async def plan_trip(request: TripRequest):
    try:
        logger.info(f"Initiating multi-agent planning pipeline for: {request.destination}")
        plan_result = await MultiAgentOrchestrator.run_pipeline(request)
        return plan_result
    except Exception as error:
        logger.exception("Error during trip planning pipeline")
        raise HTTPException(
            status_code=500,
            detail=f"Multi-Agent pipeline error: {str(error)}"
        ) from error


@app.post("/api/replan-day", response_model=DayPlan)
async def replan_day(request: SingleDayReplanRequest):
    try:
        logger.info(f"Re-planning Day {request.day} for: {request.destination}")
        updated_day = await MultiAgentOrchestrator.replan_single_day(request)
        return updated_day
    except Exception as error:
        logger.exception("Error during single day replanning")
        raise HTTPException(
            status_code=500,
            detail=f"Re-plan error: {str(error)}"
        ) from error
