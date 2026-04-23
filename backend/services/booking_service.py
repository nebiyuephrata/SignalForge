from agent.calendar.booking_flow import BookingFlow


class BookingService:
    def __init__(self) -> None:
        self.booking_flow = BookingFlow()

    def booking_link(self) -> dict[str, str]:
        return self.booking_flow.next_step()
