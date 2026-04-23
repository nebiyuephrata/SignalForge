from agent.briefs.brief_schema import OutboundMessage


class VoiceHandler:
    def enqueue(self, destination: str, message: OutboundMessage) -> dict[str, str]:
        return {"status": "stubbed", "channel": "voice", "to": destination, "preview": message.body}
