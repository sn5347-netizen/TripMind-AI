import logging
from typing import List, Dict, Any, Optional
import math

from app.models import DayPlan, Activity, DayWeather
from app.agents.weather_agent import WeatherEnvironmentalAgent
from app.services.weather_service import haversine_distance_km, estimate_transit_time_and_traffic

logger = logging.getLogger(__name__)

class ItineraryPlanningAgent:
    @staticmethod
    def plan(
        destination: str,
        days: int,
        interests: List[str],
        researched_pois: List[Dict[str, Any]],
        base_coords: Dict[str, float],
        weather_forecasts: List[DayWeather]
    ) -> List[DayPlan]:
        itinerary: List[DayPlan] = []
        poi_count = len(researched_pois)

        for day_num in range(1, days + 1):
            weather = next((w for w in weather_forecasts if w.day == day_num), None)
            day_date = weather.date if weather else None
            day_name = weather.day_of_week if weather else "Day"
            traffic_lvl = weather.traffic_level if weather else "Moderate"
            
            # Select 3 distinct activities for morning, afternoon, evening
            m_poi = researched_pois[(day_num * 3 - 3) % poi_count]
            a_poi = researched_pois[(day_num * 3 - 2) % poi_count]
            e_poi = researched_pois[(day_num * 3 - 1) % poi_count]

            base_lat = base_coords.get("lat", 12.97)
            base_lng = base_coords.get("lng", 77.59)

            m_lat = round(base_lat + float(m_poi.get("lat_offset", 0.01)), 5)
            m_lng = round(base_lng + float(m_poi.get("lng_offset", -0.01)), 5)

            a_lat = round(base_lat + float(a_poi.get("lat_offset", -0.012)), 5)
            a_lng = round(base_lng + float(a_poi.get("lng_offset", 0.014)), 5)

            e_lat = round(base_lat + float(e_poi.get("lat_offset", 0.005)), 5)
            e_lng = round(base_lng + float(e_poi.get("lng_offset", -0.006)), 5)

            # Calculate transit legs
            dist_m_to_a = haversine_distance_km(m_lat, m_lng, a_lat, a_lng)
            time_m_to_a, cond_m_to_a = estimate_transit_time_and_traffic(dist_m_to_a, day_name, "afternoon")

            dist_a_to_e = haversine_distance_km(a_lat, a_lng, e_lat, e_lng)
            time_a_to_e, cond_a_to_e = estimate_transit_time_and_traffic(dist_a_to_e, day_name, "evening")

            total_day_dist = round(dist_m_to_a + dist_a_to_e, 1)
            total_day_transit = time_m_to_a + time_a_to_e

            activities = [
                Activity(
                    name=m_poi.get("name", f"Morning Exploration in {destination}"),
                    description=m_poi.get("desc", m_poi.get("description", "Start your morning discovering iconic scenic landmarks.")),
                    category=m_poi.get("category", "nature"),
                    time_slot="morning",
                    duration_hours=2.5,
                    estimated_cost=float(m_poi.get("cost", m_poi.get("estimated_cost_inr", 200))),
                    latitude=m_lat,
                    longitude=m_lng,
                    address_or_area=f"Central district, {destination}",
                    opening_hours=m_poi.get("hours", m_poi.get("opening_hours", "08:30 - 18:00")),
                    indoor=bool(m_poi.get("indoor", False)),
                    verified_poi=True,
                    booking_link=f"https://www.google.com/maps/search/?api=1&query={m_poi.get('name', destination)}",
                    travel_time_from_previous_min=None,
                    distance_from_previous_km=None
                ),
                Activity(
                    name=a_poi.get("name", f"Afternoon Cultural Discovery"),
                    description=a_poi.get("desc", a_poi.get("description", "Immerse in heritage, local workshops, or regional cuisine.")),
                    category=a_poi.get("category", "culture"),
                    time_slot="afternoon",
                    duration_hours=3.0,
                    estimated_cost=float(a_poi.get("cost", a_poi.get("estimated_cost_inr", 350))),
                    latitude=a_lat,
                    longitude=a_lng,
                    address_or_area=f"Heritage Quarter, {destination}",
                    opening_hours=a_poi.get("hours", a_poi.get("opening_hours", "10:00 - 19:00")),
                    indoor=bool(a_poi.get("indoor", True)),
                    verified_poi=True,
                    booking_link=f"https://www.google.com/maps/search/?api=1&query={a_poi.get('name', destination)}",
                    travel_time_from_previous_min=time_m_to_a,
                    distance_from_previous_km=dist_m_to_a
                ),
                Activity(
                    name=e_poi.get("name", f"Evening Culinary & Sunset Vistas"),
                    description=e_poi.get("desc", e_poi.get("description", "Unwind at a lively promenade with authentic dining.")),
                    category=e_poi.get("category", "food"),
                    time_slot="evening",
                    duration_hours=2.5,
                    estimated_cost=float(e_poi.get("cost", e_poi.get("estimated_cost_inr", 600))),
                    latitude=e_lat,
                    longitude=e_lng,
                    address_or_area=f"Waterfront / Market Hub, {destination}",
                    opening_hours=e_poi.get("hours", e_poi.get("opening_hours", "16:00 - 23:00")),
                    indoor=bool(e_poi.get("indoor", False)),
                    verified_poi=True,
                    booking_link=f"https://www.google.com/maps/search/?api=1&query={e_poi.get('name', destination)}",
                    travel_time_from_previous_min=time_a_to_e,
                    distance_from_previous_km=dist_a_to_e
                )
            ]

            # Apply environmental weather adaptation
            adapted_activities = WeatherEnvironmentalAgent.audit_and_adapt_activities(
                weather_forecasts=weather_forecasts,
                day_number=day_num,
                activities=activities
            )

            day_cost = sum(act.estimated_cost for act in adapted_activities)
            
            day_title_prefix = f"{day_name}, {day_date}" if day_date else f"Day {day_num}"
            day_plan = DayPlan(
                day=day_num,
                date=day_date,
                day_of_week=day_name,
                title=f"Day {day_num} ({day_title_prefix}): Highlights & Discovery",
                summary=f"Balanced schedule exploring {adapted_activities[0].name} and {adapted_activities[1].name}.",
                weather=weather,
                activities=adapted_activities,
                estimated_day_cost=round(day_cost, 2),
                estimated_travel_time_min=total_day_transit,
                estimated_travel_distance_km=total_day_dist,
                traffic_level=traffic_lvl,
                traffic_summary=weather.traffic_advisory if weather and weather.traffic_advisory else f"{traffic_lvl}; est. {total_day_transit} mins transit across {total_day_dist} km.",
                transit_tips=f"{traffic_lvl}: Approx {total_day_transit} mins total drive ({total_day_dist} km). Metro/walking recommended during peak hours."
            )
            itinerary.append(day_plan)

        return itinerary
