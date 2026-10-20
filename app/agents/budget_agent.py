import logging
from typing import Dict, Any, List
from app.models import BudgetBreakdown, DayPlan

logger = logging.getLogger(__name__)

class BudgetOptimizerAgent:
    @staticmethod
    def optimize(
        budget: float,
        travelers: int,
        days: int,
        itinerary: List[DayPlan]
    ) -> BudgetBreakdown:
        per_person = round(budget / travelers, 2)
        
        # Calculate activity cost sum
        total_activity_cost_per_person = sum(
            sum(act.estimated_cost for act in day.activities)
            for day in itinerary
        )
        total_activity_cost = total_activity_cost_per_person * travelers

        # Realistic travel benchmarks (INR per person per day)
        daily_stay_est = 1800.0 * (travelers / 2.0 if travelers > 1 else 1.0)
        total_stay_est = daily_stay_est * days
        
        daily_food_est = 600.0 * travelers
        total_food_est = daily_food_est * days
        
        daily_transport_est = 400.0 * travelers
        total_transport_est = daily_transport_est * days
        
        buffer_est = round(budget * 0.08, 2)

        estimated_total_spent = round(
            total_activity_cost + total_stay_est + total_food_est + total_transport_est + buffer_est, 2
        )

        overrun = max(0.0, estimated_total_spent - budget)
        status = "within_budget" if overrun == 0 else "exceeded"

        # Allocations based on user budget
        allocation = {
            "accommodation": round(budget * 0.35, 2),
            "transport": round(budget * 0.25, 2),
            "food": round(budget * 0.20, 2),
            "activities": round(budget * 0.12, 2),
            "buffer": round(budget * 0.08, 2)
        }

        # 3 Tiers Comparison
        tier_comparison = {
            "backpacker": {
                "label": "Backpacker / Hostels & Metro",
                "estimated_total": round(budget * 0.65, 2),
                "stay_per_night": round((budget * 0.25) / days, 2),
                "daily_food": round((budget * 0.15) / days, 2),
                "style": "Shared dorms/hostels, public buses/subway, local street food"
            },
            "balanced": {
                "label": "Comfort / 3-Star Hotels & Cabs",
                "estimated_total": round(budget, 2),
                "stay_per_night": round((budget * 0.35) / days, 2),
                "daily_food": round((budget * 0.20) / days, 2),
                "style": "Boutique hotels/Airbnbs, rideshare/cabs, mid-range dining"
            },
            "luxury": {
                "label": "Premium / 5-Star Resorts & Private Chauffeur",
                "estimated_total": round(budget * 1.75, 2),
                "stay_per_night": round((budget * 0.70) / days, 2),
                "daily_food": round((budget * 0.45) / days, 2),
                "style": "Luxury resort, private chauffeur, fine-dining & VIP experiences"
            }
        }

        # Recommendations
        recommendations = [
            "Book accommodations 3-4 weeks in advance to capture 20% early-bird savings.",
            "Purchase a multi-day unlimited public transit card instead of booking point-to-point cabs.",
            "Schedule museum visits on discount days or utilize combo heritage tourist passes."
        ]
        if overrun > 0:
            recommendations.insert(
                0,
                f"Budget Warning: Estimated total exceeds requested budget by ₹{overrun:,.0f}. Consider selecting the Backpacker tier or swapping 2 paid activities with free scenic public spots."
            )

        return BudgetBreakdown(
            total_budget=budget,
            estimated_total_spent=estimated_total_spent,
            budget_per_person=per_person,
            currency="INR",
            status=status,
            overrun_amount=round(overrun, 2),
            allocation=allocation,
            tier_comparison=tier_comparison,
            cost_saving_recommendations=recommendations
        )

