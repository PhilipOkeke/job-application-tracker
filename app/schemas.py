from datetime import date, datetime

from pydantic import ConfigDict, model_validator
from sqlmodel import SQLModel

from app.models import ApplicationStatus


class ApplicationBase(SQLModel):
    company: str
    role: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    location: str = ""
    job_url: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    applied_on: date | None = None
    next_action: str = ""
    notes: str = ""

    @model_validator(mode="after")
    def validate_salary_range(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min cannot be greater than salary_max")
        return self


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(SQLModel):
    company: str | None = None
    role: str | None = None
    status: ApplicationStatus | None = None
    location: str | None = None
    job_url: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    applied_on: date | None = None
    next_action: str | None = None
    notes: str | None = None


class ApplicationRead(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AnalyticsRead(SQLModel):
    total: int
    active: int
    response_rate: float
    by_status: dict[str, int]
