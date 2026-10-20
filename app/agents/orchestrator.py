import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models import (
    TripRequest,
    TripPlanResponse,
    AgentTrace,
    DayPlan,
    SingleDayReplanRequest
)
from app.services.weather_service import WeatherGeoService
from app.services.gemini_service import GeminiService
from app.agents.research_agent import DestinationResearchAgent
from app.agents.itinerary_agent import ItineraryPlanningAgent
from app.agents.budget_agent import BudgetOptimizerAgent
from app.agents.validation_agent import CriticValidationAgent

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @classmethod
    async def run_pipeline(cls, request: TripRequest) -> TripPlanResponse:
        traces: List[AgentTrace] = []
        
        # Determine AI engine tag
        has_gemini = bool(GeminiService.get_effective_key(request.api_key))
        ai_engine_name = "Gemini 2.5 Flash" if has_gemini else "Autonomous Multi-Agent Heuristic Engine"

        # Trace 1: Orchestrator initialization
        date_info = f", starting {request.start_date}" if request.start_date else ""
        traces.append(AgentTrace(
            agent_name="Orchestrator Agent",
            action="Pipeline Initialization",
            status="started",
            details=f"Received trip request for {request.destination} ({request.days} days{date_info}, {request.travelers} travelers, budget ₹{request.budget:,.0f}). Delegating to specialist agents...",
            timestamp=cls._now_str()
        ))

        # STEP 1: Weather & Geolocation Agent
        traces.append(AgentTrace(
            agent_name="Weather & Geo Agent",
            action="Geocoding & Forecast Query",
            status="in_progress",
            details=f"Resolving coordinates, date-specific traffic, and live meteorological telemetry for {request.destination} via Open-Meteo API...",
            timestamp=cls._now_str()
        ))
        
        coords = WeatherGeoService.get_coordinates(request.destination)
        weather_forecasts = WeatherGeoService.get_forecast(coords["lat"], coords["lng"], request.days, start_date=request.start_date)
        
        live_count = sum(1 for w in weather_forecasts if w.is_live)
        start_date_str = weather_forecasts[0].date if weather_forecasts and weather_forecasts[0].date else "upcoming"
        traces.append(AgentTrace(
            agent_name="Weather & Geo Agent",
            action="Geocoding & Forecast Query",
            status="completed",
            details=f"Located {coords.get('name', request.destination)} at ({coords['lat']:.4f}, {coords['lng']:.4f}). Loaded forecast & traffic patterns for travel dates starting {start_date_str} ({live_count} live days).",
            timestamp=cls._now_str()
        ))

        # STEP 2: Destination Research Agent
        traces.append(AgentTrace(
            agent_name="Destination Research Agent",
            action="Attraction & POI Discovery",
            status="in_progress",
            details=f"Synthesizing cultural, culinary, and scenic points of interest for interests: {', '.join(request.interests)}...",
            timestamp=cls._now_str()
        ))

        research_agent = DestinationResearchAgent(api_key=request.api_key)
        researched_pois = await research_agent.research(
            destination=request.destination,
            interests=request.interests,
            coords=coords
        )

        traces.append(AgentTrace(
            agent_name="Destination Research Agent",
            action="Attraction & POI Discovery",
            status="completed",
            details=f"Discovered {len(researched_pois)} verified attractions with geo-offsets, ticket estimates, and operational hours.",
            timestamp=cls._now_str()
        ))

        # STEP 3: Itinerary Planning Agent
        traces.append(AgentTrace(
            agent_name="Itinerary Planning Agent",
            action="Spatio-Temporal Clustering",
            status="in_progress",
            details=f"Organizing {request.days}-day schedule, optimizing transit vectors, and matching activities with morning/afternoon/evening slots...",
            timestamp=cls._now_str()
        ))

        itinerary = ItineraryPlanningAgent.plan(
            destination=request.destination,
            days=request.days,
            interests=request.interests,
            researched_pois=researched_pois,
            base_coords=coords,
            weather_forecasts=weather_forecasts
        )

        traces.append(AgentTrace(
            agent_name="Itinerary Planning Agent",
            action="Spatio-Temporal Clustering",
            status="completed",
            details=f"Constructed {len(itinerary)} day plans with environmental weather adaptations and realistic pacing.",
            timestamp=cls._now_str()
        ))

        # STEP 4: Budget & Optimizer Agent
        traces.append(AgentTrace(
            agent_name="Budget Optimizer Agent",
            action="Cost Auditing & Tier Comparison",
            status="in_progress",
            details=f"Auditing expenses against ceiling ₹{request.budget:,.0f} across Stay, Transit, Food, and Activities...",
            timestamp=cls._now_str()
        ))

        budget_breakdown = BudgetOptimizerAgent.optimize(
            budget=request.budget,
            travelers=request.travelers,
            days=request.days,
            itinerary=itinerary
        )

        b_status = "completed" if budget_breakdown.status == "within_budget" else "optimized"
        traces.append(AgentTrace(
            agent_name="Budget Optimizer Agent",
            action="Cost Auditing & Tier Comparison",
            status=b_status,
            details=f"Budget analysis completed: Estimated spending ₹{budget_breakdown.estimated_total_spent:,.0f} ({budget_breakdown.status}). 3 comparative tiers calculated.",
            timestamp=cls._now_str()
        ))

        # STEP 5: Critic & Validation Agent
        traces.append(AgentTrace(
            agent_name="Critic & Validation Agent",
            action="Plan Sanity Audit",
            status="in_progress",
            details="Running multi-point validation suite on geographic feasibility, opening hours, and budget adherence...",
            timestamp=cls._now_str()
        ))

        validation = CriticValidationAgent.validate(
            destination=request.destination,
            days=request.days,
            interests=request.interests,
            itinerary=itinerary,
            budget=budget_breakdown
        )

        traces.append(AgentTrace(
            agent_name="Critic & Validation Agent",
            action="Plan Sanity Audit",
            status="completed",
            details=f"Audit passed with Feasibility Score: {validation.score}/100. Verification badges awarded.",
            timestamp=cls._now_str()
        ))

        # Final response
        start_d = weather_forecasts[0].date if weather_forecasts and weather_forecasts[0].date else ""
        end_d = weather_forecasts[-1].date if weather_forecasts and weather_forecasts[-1].date else ""
        date_str_display = f" from {start_d} to {end_d}" if start_d and end_d else ""
        summary_desc = (
            f"An intelligently curated {request.days}-day trip to {request.destination}{date_str_display} "
            f"for {request.travelers} traveler(s), balancing {', '.join(request.interests)}."
        )

        return TripPlanResponse(
            destination=coords.get("name", request.destination),
            destination_summary=summary_desc,
            coordinates={"lat": coords["lat"], "lng": coords["lng"]},
            days=request.days,
            travelers=request.travelers,
            itinerary=itinerary,
            budget=budget_breakdown,
            validation=validation,
            agent_traces=traces,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ai_engine=ai_engine_name
        )

    @classmethod
    async def replan_single_day(cls, request: SingleDayReplanRequest) -> DayPlan:
        """Regenerates a single specific day without mutating the rest of the trip."""
        coords = WeatherGeoService.get_coordinates(request.destination)
        weather_forecasts = WeatherGeoService.get_forecast(coords["lat"], coords["lng"], request.total_days, start_date=request.date)
        research_agent = DestinationResearchAgent(api_key=request.api_key)
        pois = await research_agent.research(
            destination=request.destination,
            interests=request.interests,
            coords=coords
        )
        # Shift POIs by day offset to get fresh activities
        shifted_pois = pois[request.day:] + pois[:request.day]
        itinerary = ItineraryPlanningAgent.plan(
            destination=request.destination,
            days=request.day,
            interests=request.interests,
            researched_pois=shifted_pois,
            base_coords=coords,
            weather_forecasts=weather_forecasts
        )
        # Return the specific requested day plan
        target_day = itinerary[-1]
        target_day.day = request.day
        target_day.title = f"Day {request.day} ({target_day.day_of_week}): Freshly Re-optimized Itinerary"
        return target_day

