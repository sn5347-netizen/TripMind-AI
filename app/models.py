from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    days: int = Field(ge=1, le=14)
    budget: float = Field(gt=0, le=100000000)
    travelers: int = Field(ge=1, le=20)
    interests: List[str] = Field(min_length=1, max_length=8)
    start_date: Optional[str] = Field(default=None)  # YYYY-MM-DD
    travel_pace: Optional[str] = Field(default="moderate")  # relaxed, moderate, fast-paced
    trip_type: Optional[str] = Field(default="friends_or_solo")  # solo, friends_or_solo, family, couple
    api_key: Optional[str] = Field(default=None)

class SingleDayReplanRequest(BaseModel):
    destination: str
    day: int
    total_days: int
    interests: List[str]
    date: Optional[str] = None
    weather_condition: Optional[str] = None
    reason: Optional[str] = "re-optimize"
    current_activities: Optional[List[str]] = []
    api_key: Optional[str] = None

class Activity(BaseModel):
    name: str
    description: str
    category: str  # culture, nature, food, adventure, shopping, relaxation
    time_slot: str  # morning, afternoon, evening
    duration_hours: float = 2.0
    estimated_cost: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_or_area: Optional[str] = None
    opening_hours: Optional[str] = "09:00 - 18:00"
    indoor: bool = False
    verified_poi: bool = False
    booking_link: Optional[str] = None
    weather_tag: Optional[str] = "Good for all weather"
    travel_time_from_previous_min: Optional[int] = None
    distance_from_previous_km: Optional[float] = None

class DayWeather(BaseModel):
    day: int
    date: Optional[str] = None
    day_of_week: Optional[str] = None
    condition: str
    max_temp_c: float
    min_temp_c: float
    precipitation_probability: int
    advisory: str
    traffic_level: Optional[str] = "Moderate"
    traffic_advisory: Optional[str] = None
    is_live: bool = False

class DayPlan(BaseModel):
    day: int
    date: Optional[str] = None
    day_of_week: Optional[str] = None
    title: str
    summary: str
    weather: Optional[DayWeather] = None
    activities: List[Activity]
    estimated_day_cost: float = 0.0
    estimated_travel_time_min: int = 40
    estimated_travel_distance_km: float = 8.5
    traffic_level: str = "Moderate"
    traffic_summary: str = "Standard city flow; 15-25 min between clustered stops."
    transit_tips: str = "Use local metro, cabs or walking between clustered spots."

class BudgetBreakdown(BaseModel):
    total_budget: float
    estimated_total_spent: float
    budget_per_person: float
    currency: str = "INR"
    status: str = "within_budget"  # within_budget, exceeded, optimal
    overrun_amount: float = 0.0
    allocation: Dict[str, float]
    tier_comparison: Dict[str, Dict[str, Any]]
    cost_saving_recommendations: List[str] = []

class AgentTrace(BaseModel):
    agent_name: str
    action: str
    status: str  # started, completed, alert, warning
    details: str
    timestamp: str

class ValidationResult(BaseModel):
    valid: bool
    score: int = 95  # out of 100
    checks: List[str]
    notices: List[str]
    verified_data_count: int = 0
    estimated_data_count: int = 0

class TripPlanResponse(BaseModel):
    destination: str
    destination_summary: str
    coordinates: Dict[str, float]  # {"lat": ..., "lng": ...}
    days: int
    travelers: int
    itinerary: List[DayPlan]
    budget: BudgetBreakdown
    validation: ValidationResult
    agent_traces: List[AgentTrace]
    generated_at: str
    ai_engine: str
