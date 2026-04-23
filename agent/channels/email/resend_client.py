from agent.briefs.brief_schema import OutboundMessage


class ResendClient:
    def send(self, to_email: str, message: OutboundMessage) -> dict[str, str]:
        return {"status": "stubbed", "channel": "email", "to": to_email, "preview": message.body}
