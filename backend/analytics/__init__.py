from .insights import generate_structured_insights
from .statistics import compute_descriptive_stats

# Limits what from backend.analytics import * exposes (if someone uses that style) 
__all__ = ["generate_structured_insights", "compute_descriptive_stats"]
