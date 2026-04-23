def can_send_sms(has_opt_in: bool, stop_requested: bool) -> bool:
    return has_opt_in and not stop_requested
