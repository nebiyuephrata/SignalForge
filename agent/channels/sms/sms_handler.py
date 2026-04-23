from agent.briefs.brief_schema import OutboundMessage
from agent.channels.sms.africas_talking_client import AfricasTalkingClient


class SMSHandler:
    def __init__(self) -> None:
        self.client = AfricasTalkingClient()

    def send(self, phone_number: str, message: OutboundMessage) -> dict[str, str]:
        return self.client.send(phone_number, message)
