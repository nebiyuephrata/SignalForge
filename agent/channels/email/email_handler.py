from agent.briefs.brief_schema import OutboundMessage
from agent.channels.email.resend_client import ResendClient


class EmailHandler:
    def __init__(self) -> None:
        self.client = ResendClient()

    def send(self, to_email: str, message: OutboundMessage) -> dict[str, str]:
        return self.client.send(to_email, message)
