class VoiceHandler:
    def enqueue(self, destination: str, message_body: str) -> dict[str, str]:
        return {"status": "stubbed", "channel": "voice", "to": destination, "preview": message_body}
