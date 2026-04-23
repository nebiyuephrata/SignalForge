from agent.calendar.cal_client import CalClient


class BookingFlow:
    def __init__(self) -> None:
        self.client = CalClient()

    def next_step(self, *, company_name: str | None = None, contact_email: str | None = None) -> dict[str, str]:
        return {"booking_url": self.client.booking_link(company_name=company_name, contact_email=contact_email)}
