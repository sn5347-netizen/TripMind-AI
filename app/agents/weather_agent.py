import logging
from typing import List, Dict, Any
from app.models import DayWeather, Activity

logger = logging.getLogger(__name__)

class WeatherEnvironmentalAgent:
    @staticmethod
    def audit_and_adapt_activities(
        weather_forecasts: List[DayWeather], 
        day_number: int,
        activities: List[Activity]
    ) -> List[Activity]:
        """
        Examines weather for the day. If high rain probability (>50%) or extreme conditions,
        adapts outdoor activities with indoor equivalents or flags appropriate gear.
        """
        forecast = next((w for w in weather_forecasts if w.day == day_number), None)
        if not forecast:
            return activities

        adapted_activities = []
        is_rainy = "Rain" in forecast.condition or "Drizzle" in forecast.condition or forecast.precipitation_probability >= 50
        is_hot = forecast.max_temp_c >= 35.0

        for act in activities:
            updated_act = act.model_copy()
            
            if is_rainy and not act.indoor:
                updated_act.weather_tag = f"🌧️ Weather Advisory: High rain chance ({forecast.precipitation_probability}%). Covered venue/umbrella advised."
            elif is_hot and not act.indoor:
                updated_act.weather_tag = f"☀️ Heat Advisory: High of {forecast.max_temp_c}°C. Recommended during early morning/evening."
            else:
                updated_act.weather_tag = f"✨ Ideal Conditions: {forecast.condition} ({forecast.min_temp_c}°C - {forecast.max_temp_c}°C)"
                
            adapted_activities.append(updated_act)

        return adapted_activities

