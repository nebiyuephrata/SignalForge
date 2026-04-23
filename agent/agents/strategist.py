from agent.briefs.brief_schema import LeadBrief
from agent.core.routing import route_next_action


class StrategistAgent:
    def run(self, brief: LeadBrief) -> dict[str, str]:
        crm_fields = route_next_action(brief)
        if crm_fields.next_action == "ask_clarifying_question":
            angle = "validate whether the detected hiring or compliance signals are relevant right now"
        elif crm_fields.next_action == "send_insight_hook":
            angle = "lead with a signal-backed observation and a narrow qualification question"
        else:
            angle = "move from verified insight into a concrete booking invitation"
        return {"strategic_angle": angle}
