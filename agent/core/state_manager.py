from typing import Literal

from pydantic import BaseModel

from agent.briefs.brief_schema import LeadBrief


class LeadState(BaseModel):
    awareness: Literal["cold", "aware", "engaged"] = "cold"
    qualification: Literal["unknown", "partial", "qualified"] = "unknown"
    intent: Literal["low", "medium", "high"] = "low"
    brief: LeadBrief
