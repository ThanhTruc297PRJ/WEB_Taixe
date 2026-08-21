from datetime import datetime

from pydantic import BaseModel


class ConsentBase(BaseModel):
    consent_type: str
    accepted: bool


class ConsentCreate(ConsentBase):
    pass


class Consent(ConsentBase):
    id: str
    user_id: str
    updated_at: datetime
