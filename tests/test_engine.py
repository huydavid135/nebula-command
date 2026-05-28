from nebula_command.connectors import pulses_frame
from nebula_command.engine import export_markdown, generate_mission, scenario_matrix
from nebula_command.models import AssetPulse


def sample_pulses():
    return [
        AssetPulse("BTC", 100000, 70, 80, 75, 35, 40, "TEST"),
        AssetPulse("ETH", 4000, 55, 68, 60, 45, 50, "TEST"),
        AssetPulse("SOL", 180, 40, 55, 45, 80, 78, "TEST"),
    ]


def test_mission_has_orders():
    plan = generate_mission("ETF flow", sample_pulses(), 10000, "Balanced")
    assert plan.stance in {"ACCUMULATE", "OBSERVE", "DEFENSIVE"}
    assert len(plan.reasoning) >= 3


def test_scenario_matrix():
    df = scenario_matrix(sample_pulses(), "ETF inflow surge", 10000)
    assert set(["asset", "adjusted_score", "paper_exposure_usd"]).issubset(df.columns)
    assert len(df) == 3


def test_export_report():
    plan = generate_mission("test", sample_pulses(), 10000, "Stealth")
    report = export_markdown(plan)
    assert "Nebula Command Strategy Report" in report
