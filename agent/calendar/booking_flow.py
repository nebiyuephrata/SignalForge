from agent.calendar.cal_client import CalClient


class BookingFlow:
    def __init__(self) -> None:
        self.client = CalClient()

    def next_step(self) -> dict[str, str]:
        return {"booking_url": self.client.booking_link()}
