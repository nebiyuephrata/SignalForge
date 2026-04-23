from agent.briefs.brief_schema import OutboundMessage


class AfricasTalkingClient:
    def send(self, phone_number: str, message: OutboundMessage) -> dict[str, str]:
        return {"status": "stubbed", "channel": "sms", "to": phone_number, "preview": message.body}
