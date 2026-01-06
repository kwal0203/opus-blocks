from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertEventRead(BaseModel):
    id: str
    name: str
    status: str
    value: float | None
    threshold: float | None
    context_json: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
