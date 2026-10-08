import pytest
from app.services.gaps import (
    priority_score,
    _gap_severity,
    _student_gap_status,
    PRIORITY_WEIGHTS,
)


class TestPriorityScoring:
    def test_weights_sum(self):
        assert abs(sum(PRIORITY_WEIGHTS.values()) - 1.0) < 1e-6

    def test_priority_max(self):
        score = priority_score(1.0, 1.0, 1.0, 1.0)
        assert score == 100.0

    def test_priority_zero(self):
        score = priority_score(0.0, 0.0, 0.0, 0.0)
        assert score == 0.0

    def test_priority_missing_skill_high_demand(self):
        # missing skill, high demand, high role relevance, medium confidence
        score = priority_score(0.9, 1.0, 1.0, 0.8)
        assert score > 80.0

    def test_priority_partial_skill_low_demand(self):
        score = priority_score(0.2, 0.5, 0.4, 0.5)
        assert score < 40.0


class TestGapSeverity:
    def test_none_is_full_gap(self):
        assert _gap_severity("none") == 1.0

    def test_beginner_partial(self):
        assert 0.3 < _gap_severity("beginner") < 0.5

    def test_intermediate_nearly_there(self):
        assert _gap_severity("intermediate") < 0.4

    def test_advanced_no_gap(self):
        assert _gap_severity("advanced") == 0.0

    def test_same_level_no_gap(self):
        assert _gap_severity("intermediate", required_level="intermediate") == 0.0


class TestStudentGapStatus:
    def test_none_missing(self):
        assert _student_gap_status("none") == "missing"

    def test_beginner_partial(self):
        assert _student_gap_status("beginner") == "partial"

    def test_intermediate_partial(self):
        assert _student_gap_status("intermediate") == "partial"

    def test_advanced_partial(self):
        assert _student_gap_status("advanced") == "partial"
