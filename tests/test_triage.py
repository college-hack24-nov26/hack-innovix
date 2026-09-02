from app.services.triage_service import RedFlagEngine


def test_emergency_chest_and_breath():
    level, _ = RedFlagEngine().evaluate({"chief_complaint": "chest pain", "associated": "breathing difficulty"})
    assert level == "EMERGENCY"


def test_low_when_empty():
    level, _ = RedFlagEngine().evaluate({"chief_complaint": "routine checkup"})
    assert level == "LOW"
