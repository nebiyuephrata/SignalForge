from __future__ import annotations

from statistics import mean

from agent.core.models import ConfidenceAssessment, ConfidenceBehavior, CompetitorGapBrief, HiringSignalBrief


THRESHOLDS = {
    "high": 0.8,
    "medium": 0.6,
    "low": 0.0,
}


class ConfidenceCalibrationLayer:
    """Translate evidence quality into runtime behavior.

    This layer exists because the failure mode we most want to avoid is not
    "bad writing", it is confident writing on weak evidence. The score drives
    both prompt conditioning and channel eligibility.
    """

    def assess(
        self,
        hiring_signal_brief: HiringSignalBrief | dict[str, object],
        competitor_gap_brief: CompetitorGapBrief | dict[str, object],
    ) -> ConfidenceAssessment:
        if isinstance(hiring_signal_brief, dict):
            hiring_signal_brief = HiringSignalBrief.model_validate(hiring_signal_brief)
        if isinstance(competitor_gap_brief, dict):
            competitor_gap_brief = CompetitorGapBrief.model_validate(competitor_gap_brief)
        signal_confidences = [signal.confidence for signal in hiring_signal_brief.signals]
        hiring_average = mean(signal_confidences) if signal_confidences else 0.0
        competitor_confidence = competitor_gap_brief.confidence
        source_success_rate = (
            sum(1 for source in hiring_signal_brief.data_sources_checked if source.status == "success")
            / max(len(hiring_signal_brief.data_sources_checked), 1)
        )
        contradiction_penalty = 0.12 if "layoff_overrides_funding" in hiring_signal_brief.uncertainty_flags else 0.0
        weak_signal_penalty = 0.08 if "weak_hiring_velocity_signal" in hiring_signal_brief.uncertainty_flags else 0.0
        sparse_sector_penalty = 0.05 if competitor_gap_brief.sparse_sector else 0.0

        numeric_score = round(
            (
                hiring_signal_brief.overall_confidence * 0.5
                + hiring_average * 0.2
                + competitor_confidence * 0.15
                + source_success_rate * 0.15
            )
            - contradiction_penalty
            - weak_signal_penalty
            - sparse_sector_penalty,
            2,
        )
        bounded_score = min(max(numeric_score, 0.0), 1.0)
        level = self._level_for_score(bounded_score)

        rationale = [
            f"Hiring brief confidence contributed {hiring_signal_brief.overall_confidence:.2f}.",
            f"Average signal confidence contributed {hiring_average:.2f}.",
            f"Competitor gap confidence contributed {competitor_confidence:.2f}.",
            f"Source success rate contributed {source_success_rate:.2f}.",
        ]
        if contradiction_penalty:
            rationale.append("Applied contradiction penalty because layoffs and hiring signals conflict.")
        if weak_signal_penalty:
            rationale.append("Applied weak-signal penalty because hiring velocity is not strong enough for assertive phrasing.")
        if sparse_sector_penalty:
            rationale.append("Applied sparse-sector penalty because fewer than five competitors were available.")

        return ConfidenceAssessment(
            numeric_score=bounded_score,
            level=level,
            thresholds=THRESHOLDS,
            behavior=self._behavior_for_level(level),
            rationale=rationale,
            uncertainty_flags=list(
                dict.fromkeys(
                    [
                        flag
                        for flag in [
                            *hiring_signal_brief.uncertainty_flags,
                            "sparse_sector" if competitor_gap_brief.sparse_sector else None,
                        ]
                        if flag
                    ]
                )
            ),
        )

    def _level_for_score(self, score: float) -> str:
        if score >= THRESHOLDS["high"]:
            return "high"
        if score >= THRESHOLDS["medium"]:
            return "medium"
        return "low"

    @staticmethod
    def _behavior_for_level(level: str) -> ConfidenceBehavior:
        if level == "high":
            return ConfidenceBehavior(
                tone="assertive",
                max_claims=3,
                allow_booking_link=True,
                allow_sms=True,
                require_question_led_copy=False,
            )
        if level == "medium":
            return ConfidenceBehavior(
                tone="directional",
                max_claims=2,
                allow_booking_link=True,
                allow_sms=True,
                require_question_led_copy=False,
            )
        return ConfidenceBehavior(
            tone="exploratory",
            max_claims=1,
            allow_booking_link=False,
            allow_sms=False,
            require_question_led_copy=True,
        )


def compute_global_confidence(hiring_signal_brief: dict[str, object]) -> str:
    """Backward-compatible helper used by older tests and scripts."""

    overall_confidence = float(hiring_signal_brief.get("overall_confidence", 0.0) or 0.0)
    if overall_confidence >= THRESHOLDS["high"]:
        return "high"
    if overall_confidence >= THRESHOLDS["medium"]:
        return "medium"
    return "low"
