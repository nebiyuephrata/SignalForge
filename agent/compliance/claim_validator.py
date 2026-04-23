from agent.briefs.brief_schema import OutboundMessage


def validate_message(message: OutboundMessage) -> list[str]:
    warnings: list[str] = []
    if message.crm_fields.signal_confidence < 0.4 and "verified" in message.body.lower():
        warnings.append("Low-confidence messages should not use high-certainty language.")
    if len(message.body.split()) > 120:
        warnings.append("Message exceeds the 120-word guardrail.")
    return warnings
