from agent.briefs.brief_schema import CRMFields, LeadBrief
from agent.signals.ai_maturity import score_ai_maturity
from agent.signals.confidence_scoring import average_confidence


def classify_icp(brief: LeadBrief) -> str:
    if brief.lead.industry:
        return f"{brief.lead.industry.lower()}-accounts"
    return "unclassified"


def route_next_action(brief: LeadBrief) -> CRMFields:
    signal_confidence = average_confidence(
        brief.hiring.signals + brief.compliance.signals + brief.ai_maturity.signals + brief.competitor_gap.signals
    )
    ai_maturity = score_ai_maturity(brief.ai_maturity.signals)
    if signal_confidence < 0.4:
        return CRMFields(
            icp_segment=classify_icp(brief),
            signal_confidence=signal_confidence,
            ai_maturity=ai_maturity,
            intent_level="low",
            qualification_status="exploratory",
            next_action="ask_clarifying_question",
        )
    if signal_confidence < 0.75:
        return CRMFields(
            icp_segment=classify_icp(brief),
            signal_confidence=signal_confidence,
            ai_maturity=ai_maturity,
            intent_level="medium",
            qualification_status="partial",
            next_action="send_insight_hook",
        )
    return CRMFields(
        icp_segment=classify_icp(brief),
        signal_confidence=signal_confidence,
        ai_maturity=ai_maturity,
        intent_level="high",
        qualification_status="qualified",
        next_action="book_meeting",
    )
