from agent.signals.ai_maturity import collect_ai_maturity_inputs, score_ai_maturity_inputs
from agent.signals.competitor_gap_service import CompetitorGapService
from agent.tools.competitor_analysis import CompetitorAnalysisTool
from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.tools.job_scraper import JobScraper


def test_ai_maturity_scorer_uses_structured_weighted_inputs() -> None:
    company = CrunchbaseTool().lookup_company_record("Northstar Lending")
    assert company is not None

    inputs = collect_ai_maturity_inputs(
        company,
        role_titles=["Machine Learning Engineer", "Data Infrastructure Engineer"],
    )
    assessment = score_ai_maturity_inputs(inputs)

    assert assessment.score in {0, 1, 2, 3}
    assert assessment.max_points == 12
    assert assessment.weighted_points >= 0
    assert any(justification.weight == "high" for justification in assessment.justifications)


def test_ai_maturity_scorer_handles_silent_company_as_zero_without_overclaiming() -> None:
    assessment = score_ai_maturity_inputs(collect_ai_maturity_inputs(None))

    assert assessment.score == 0
    assert assessment.confidence == 0.35
    assert "absence of evidence is not proof of absence" in assessment.explanation.lower()


def test_job_scraper_records_public_page_and_robots_policy() -> None:
    result = JobScraper(CrunchbaseTool()).scrape_company_jobs("Northstar Lending")
    source_artifact = result["source_artifact"]

    assert source_artifact["company_careers_page"]["public_only"] is True
    assert source_artifact["company_careers_page"]["respects_robots_txt"] is True
    assert source_artifact["linkedin_public"]["status"] == "skipped"


def test_competitor_gap_service_handles_sparse_sector_case() -> None:
    class SparseCrunchbase(CrunchbaseTool):
        def load_dataset(self) -> list[dict[str, object]]:  # type: ignore[override]
            return [
                {
                    "company_name": "Sparse Target",
                    "domain": "sparse-target.example",
                    "employee_count": 200,
                    "industry": "Insurtech",
                    "location": "Remote",
                    "last_funding_round": "Series A",
                    "funding_date": "2026-02-01",
                    "open_roles_current": 4,
                    "open_roles_60_days_ago": 2,
                    "ai_roles_open": 1,
                    "ai_practices": ["workflow automation"],
                    "career_page_path": "",
                    "leadership_changes": [],
                },
                {
                    "company_name": "Sparse Peer One",
                    "domain": "sparse-peer-1.example",
                    "employee_count": 210,
                    "industry": "Insurtech",
                    "location": "Remote",
                    "last_funding_round": "Series A",
                    "funding_date": "2026-01-15",
                    "open_roles_current": 5,
                    "open_roles_60_days_ago": 3,
                    "ai_roles_open": 2,
                    "ai_practices": ["claims automation"],
                    "career_page_path": "",
                    "leadership_changes": [],
                },
                {
                    "company_name": "Sparse Peer Two",
                    "domain": "sparse-peer-2.example",
                    "employee_count": 190,
                    "industry": "Insurtech",
                    "location": "Remote",
                    "last_funding_round": "Seed",
                    "funding_date": "2025-12-15",
                    "open_roles_current": 2,
                    "open_roles_60_days_ago": 1,
                    "ai_roles_open": 0,
                    "ai_practices": [],
                    "career_page_path": "",
                    "leadership_changes": [],
                },
            ]

    service = CompetitorGapService(SparseCrunchbase())
    brief = service.build("Sparse Target")

    assert brief["sparse_sector"] is True
    assert len(brief["selected_peers"]) < 5
    assert brief["distribution_position"]["label"] in {"top_quartile", "upper_mid", "lower_mid", "bottom_quartile"}


def test_competitor_selection_targets_five_to_ten_when_available() -> None:
    selected = CompetitorAnalysisTool(CrunchbaseTool()).similar_companies("Northstar Lending", min_candidates=5, max_candidates=10)

    assert 5 <= len(selected) <= 10
