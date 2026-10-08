import pytest
from app.services.demand import (
    compute_demand_score,
    demand_confidence_flag,
    DEMAND_WEIGHTS,
)


class TestDemandFormula:
    def test_default_weights_sum_to_one(self):
        assert abs(sum(DEMAND_WEIGHTS.values()) - 1.0) < 1e-6

    def test_demand_score_frequency_only(self):
        score = compute_demand_score(1.0, 0.0, 0.0, 0.0)
        expected = DEMAND_WEIGHTS["frequency"]
        assert abs(score - expected) < 1e-6

    def test_demand_score_all_one(self):
        score = compute_demand_score(1.0, 1.0, 1.0, 1.0)
        assert abs(score - 1.0) < 1e-6

    def test_demand_score_zero(self):
        score = compute_demand_score(0.0, 0.0, 0.0, 0.0)
        assert abs(score) < 1e-6

    def test_custom_weights(self):
        custom = {"frequency": 0.8, "recency": 0.1, "role_relevance": 0.1, "sector_relevance": 0.0}
        score = compute_demand_score(0.5, 1.0, 1.0, 1.0, weights=custom)
        expected = 0.8 * 0.5 + 0.1 * 1.0 + 0.1 * 1.0 + 0.0 * 1.0
        assert abs(score - expected) < 1e-6


class TestDemandConfidence:
    def test_high(self):
        assert demand_confidence_flag(30) == "high"
        assert demand_confidence_flag(100) == "high"

    def test_medium(self):
        assert demand_confidence_flag(10) == "medium"
        assert demand_confidence_flag(29) == "medium"

    def test_low(self):
        assert demand_confidence_flag(5) == "low"
        assert demand_confidence_flag(0) == "low"
