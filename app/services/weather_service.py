import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import json
import math

try:
    import httpx
except ImportError:
    httpx = None

import urllib.request
import urllib.parse

from app.models import DayWeather

logger = logging.getLogger(__name__)

# Fallback coordinates for common destinations
KNOWN_DESTINATIONS = {
    "kerala": {"lat": 9.9312, "lng": 76.2673, "name": "Kerala, India"},
    "mumbai": {"lat": 19.0760, "lng": 72.8777, "name": "Mumbai, India"},
    "delhi": {"lat": 28.6139, "lng": 77.2090, "name": "Delhi, India"},
    "goa": {"lat": 15.2993, "lng": 74.1240, "name": "Goa, India"},
    "jaipur": {"lat": 26.9124, "lng": 75.7873, "name": "Jaipur, India"},
    "manali": {"lat": 32.2432, "lng": 77.1892, "name": "Manali, Himachal Pradesh"},
    "paris": {"lat": 48.8566, "lng": 2.3522, "name": "Paris, France"},
    "tokyo": {"lat": 35.6762, "lng": 139.6503, "name": "Tokyo, Japan"},
    "london": {"lat": 51.5074, "lng": -0.1278, "name": "London, UK"},
    "new york": {"lat": 40.7128, "lng": -74.0060, "name": "New York, USA"},
    "dubai": {"lat": 25.2048, "lng": 55.2708, "name": "Dubai, UAE"},
    "bangkok": {"lat": 13.7563, "lng": 100.5018, "name": "Bangkok, Thailand"},
    "singapore": {"lat": 1.3521, "lng": 103.8198, "name": "Singapore"},
    "bali": {"lat": -8.4095, "lng": 115.1889, "name": "Bali, Indonesia"},
    "rome": {"lat": 41.9028, "lng": 12.4964, "name": "Rome, Italy"}
}

WMO_WEATHER_CODES = {
    0: ("Sunny & Clear", "Excellent for outdoor sightseeing, hiking, and open-air photography."),
    1: ("Mainly Clear", "Great weather for outdoor exploration with light breeze."),
    2: ("Partly Cloudy", "Comfortable temperature, ideal for walking tours and gardens."),
    3: ("Overcast", "Pleasant diffuse lighting; great for outdoor monuments and scenic views."),
    45: ("Foggy", "Early morning haze; take care with driving, great for moody atmospheric shots."),
    48: ("Rime Fog", "Chilly foggy conditions, dress in warm layers."),
    51: ("Light Drizzle", "Carry a light umbrella; outdoor tours still enjoyable."),
    53: ("Moderate Drizzle", "Intermittent drizzle; good time for covered bazaars and cafes."),
    55: ("Dense Drizzle", "Wear waterproof gear; prioritize covered monuments."),
    61: ("Slight Rain", "Light rain showers; keep umbrellas handy, consider museums for the afternoon."),
    63: ("Moderate Rain", "Rain showers expected; good for indoor cultural museums, galleries and food tours."),
    65: ("Heavy Rain", "Heavy downpour expected; avoid steep outdoor trails, prioritize indoor experiences."),
    71: ("Slight Snow", "Snow flurries; picturesque views, wear insulated boots."),
    73: ("Moderate Snow", "Snowfall likely; ensure thermal clothing for outdoor activities."),
    75: ("Heavy Snow", "Heavy snowfall; perfect for winter sports or cozy indoor experiences."),
    80: ("Scattered Showers", "Passing showers with sun breaks; flexible schedule recommended."),
    95: ("Thunderstorm", "Thunderstorms possible; stay indoors during peak storm hours.")
}

def _http_get_json(url: str, timeout: float = 4.0) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TripMind-AI-Planner/2.0 (student-portfolio-project)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"HTTP GET failed for {url}: {e}")
    return None

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance in kilometers between two GPS coordinates."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_transit_time_and_traffic(
    dist_km: float, 
    day_of_week: str, 
    time_slot: str
) -> Tuple[int, str]:
    """
    Calculates realistic driving/transit time in minutes and traffic condition
    based on distance, day of week, and time slot.
    """
    is_weekend = day_of_week.lower() in ("saturday", "sunday")
    is_friday = day_of_week.lower() == "friday"

    # Base average city speed in km/h
    base_speed_kmh = 24.0
    buffer_min = 6  # boarding/parking buffer

    if is_weekend:
        if time_slot == "evening" or time_slot == "afternoon":
            speed_kmh = 16.0  # tourist/weekend traffic
            condition = "Weekend Tourist Congestion"
            buffer_min = 10
        else:
            speed_kmh = 28.0  # light morning
            condition = "Light Weekend Flow"
    elif is_friday and time_slot == "evening":
        speed_kmh = 14.0  # heavy weekend exodus
        condition = "Peak Friday Evening Rush"
        buffer_min = 12
    else:
        # Weekdays Mon-Thu
        if time_slot == "morning":
            speed_kmh = 18.0  # morning commute
            condition = "Morning Commute Rush"
            buffer_min = 8
        elif time_slot == "evening":
            speed_kmh = 17.0  # evening commute
            condition = "Evening Commute Rush"
            buffer_min = 10
        else:
            speed_kmh = 26.0  # smooth midday
            condition = "Moderate Normal Flow"

    travel_minutes = max(10, int((dist_km / max(speed_kmh, 10.0)) * 60) + buffer_min)
    return travel_minutes, condition

class WeatherGeoService:
    @staticmethod
    def get_coordinates(destination: str) -> Dict[str, Any]:
        dest_clean = destination.strip().lower()
        
        # Check known dictionary first
        for key, coords in KNOWN_DESTINATIONS.items():
            if key in dest_clean:
                return coords
                
        # Try Open-Meteo Geocoding API
        try:
            encoded_query = urllib.parse.quote(destination.strip())
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_query}&count=1&language=en&format=json"
            data = _http_get_json(url, timeout=3.5)
            if data and "results" in data and len(data["results"]) > 0:
                res = data["results"][0]
                return {
                    "lat": float(res["latitude"]),
                    "lng": float(res["longitude"]),
                    "name": f"{res.get('name', destination)}, {res.get('country', '')}".strip(", ")
                }
        except Exception as e:
            logger.warning(f"Geocoding failed for {destination}: {e}")
            
        # Default fallback coordinates
        return {"lat": 12.9716, "lng": 77.5946, "name": destination}

    @classmethod
    def get_forecast(
        cls, 
        lat: float, 
        lng: float, 
        days: int, 
        start_date: Optional[str] = None
    ) -> List[DayWeather]:
        # Parse or default start_date
        today = date.today()
        if start_date:
            try:
                parsed_start = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
            except Exception:
                parsed_start = today + timedelta(days=1)
        else:
            parsed_start = today + timedelta(days=1)

        end_date = parsed_start + timedelta(days=days - 1)
        start_str = parsed_start.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        forecasts: List[DayWeather] = []
        days_from_today = (parsed_start - today).days

        # Open-Meteo standard forecast covers up to 14-16 days ahead
        if 0 <= days_from_today <= 14:
            try:
                url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lng}&daily=weathercode,temperature_2m_max,temperature_2m_min,"
                    f"precipitation_probability_max&start_date={start_str}&end_date={end_str}&timezone=auto"
                )
                data = _http_get_json(url, timeout=4.0)
                if data and "daily" in data:
                    daily = data["daily"]
                    weather_codes = daily.get("weathercode", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])
                    precip_probs = daily.get("precipitation_probability_max", [])

                    for i in range(min(days, len(weather_codes))):
                        code = weather_codes[i]
                        cond_name, advisory = WMO_WEATHER_CODES.get(
                            code, ("Partly Cloudy", "Mild pleasant weather expected.")
                        )
                        day_dt = parsed_start + timedelta(days=i)
                        day_name = day_dt.strftime("%A")
                        
                        # Compute traffic profile
                        traffic_lvl, traffic_adv = cls._get_traffic_profile(day_dt)

                        forecasts.append(
                            DayWeather(
                                day=i + 1,
                                date=day_dt.strftime("%Y-%m-%d"),
                                day_of_week=day_name,
                                condition=cond_name,
                                max_temp_c=round(float(max_temps[i]), 1) if i < len(max_temps) and max_temps[i] is not None else 28.0,
                                min_temp_c=round(float(min_temps[i]), 1) if i < len(min_temps) and min_temps[i] is not None else 19.0,
                                precipitation_probability=int(precip_probs[i]) if i < len(precip_probs) and precip_probs[i] is not None else 10,
                                advisory=advisory,
                                traffic_level=traffic_lvl,
                                traffic_advisory=traffic_adv,
                                is_live=True
                            )
                        )
            except Exception as e:
                logger.warning(f"Open-Meteo live forecast for dates failed: {e}")

        # If live forecast didn't cover all days or dates are further out, generate seasonal climatological forecast
        while len(forecasts) < days:
            d_idx = len(forecasts)
            day_dt = parsed_start + timedelta(days=d_idx)
            day_name = day_dt.strftime("%A")
            month = day_dt.strftime("%B")

            cond_pattern = [
                ("Sunny & Pleasant", f"Clear skies typical for {month}; optimal for sightseeing."),
                ("Partly Cloudy", f"Great daylight with comfortable breeze; ideal for markets and walking."),
                ("Warm & Bright", f"Sun protection and hydration recommended for mid-day excursions."),
                ("Mild & Clear", f"Cool, crisp evening conditions for dining and scenic strolls.")
            ]
            c_name, adv = cond_pattern[d_idx % len(cond_pattern)]
            traffic_lvl, traffic_adv = cls._get_traffic_profile(day_dt)

            forecasts.append(
                DayWeather(
                    day=d_idx + 1,
                    date=day_dt.strftime("%Y-%m-%d"),
                    day_of_week=day_name,
                    condition=c_name,
                    max_temp_c=29.0,
                    min_temp_c=21.0,
                    precipitation_probability=15,
                    advisory=adv,
                    traffic_level=traffic_lvl,
                    traffic_advisory=traffic_adv,
                    is_live=False
                )
            )

        return forecasts

    @staticmethod
    def _get_traffic_profile(dt: date) -> Tuple[str, str]:
        """Determines traffic level and actionable transit advisory based on day of week."""
        weekday = dt.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun

        if weekday == 5:  # Saturday
            return (
                "Weekend Tourist Congestion",
                "Peak weekend traffic around scenic viewpoints and markets between 16:00 and 21:00. Arrive by 09:30 AM to beat queues."
            )
        elif weekday == 6:  # Sunday
            return (
                "Sunday Leisure Traffic",
                "Smooth morning flow, but heavy evening return traffic on major thoroughfares between 17:30 and 20:30."
            )
        elif weekday == 4:  # Friday
            return (
                "Friday Evening Peak Rush",
                "Commuter and weekend getaway rush from 16:30 to 20:30. Walking or metro transit recommended between clustered spots."
            )
        else:  # Mon - Thu
            return (
                "Weekday Commute Flow",
                "Morning rush (08:30-10:00) & evening rush (17:30-19:30). Midday transit (11:00-16:00) is fast and smooth."
            )
