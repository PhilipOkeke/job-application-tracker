from datetime import UTC, date, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class JobApplication(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company: str = Field(index=True, min_length=1, max_length=120)
    role: str = Field(index=True, min_length=1, max_length=160)
    status: ApplicationStatus = Field(default=ApplicationStatus.SAVED, index=True)
    location: str = Field(default="", max_length=160)
    job_url: str = Field(default="", max_length=500)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    applied_on: date | None = None
    next_action: str = Field(default="", max_length=240)
    notes: str = Field(default="", max_length=4000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
