from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, func, select

from app.database import create_db_and_tables, get_session
from app.models import ApplicationStatus, JobApplication
from app.schemas import AnalyticsRead, ApplicationCreate, ApplicationRead, ApplicationUpdate

SessionDep = Annotated[Session, Depends(get_session)]
StatusFilter = Annotated[ApplicationStatus | None, Query(alias="status")]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Job Application Tracker",
    version="1.0.0",
    description="A portfolio-ready application tracker with analytics and a responsive UI.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/api/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def create_application(payload: ApplicationCreate, session: SessionDep) -> JobApplication:
    application = JobApplication.model_validate(payload)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


@app.get("/api/applications", response_model=list[ApplicationRead], tags=["applications"])
def list_applications(
    session: SessionDep,
    application_status: StatusFilter = None,
    search: str | None = None,
    offset: Offset = 0,
    limit: Limit = 50,
) -> list[JobApplication]:
    statement = select(JobApplication)
    if application_status:
        statement = statement.where(JobApplication.status == application_status)
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            (JobApplication.company.ilike(term)) | (JobApplication.role.ilike(term))
        )
    statement = statement.order_by(JobApplication.updated_at.desc()).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def get_application_or_404(application_id: int, session: Session) -> JobApplication:
    application = session.get(JobApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@app.get(
    "/api/applications/{application_id}",
    response_model=ApplicationRead,
    tags=["applications"],
)
def get_application(application_id: int, session: SessionDep) -> JobApplication:
    return get_application_or_404(application_id, session)


@app.patch(
    "/api/applications/{application_id}",
    response_model=ApplicationRead,
    tags=["applications"],
)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    session: SessionDep,
) -> JobApplication:
    application = get_application_or_404(application_id, session)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(application, key, value)
    if (
        application.salary_min is not None
        and application.salary_max is not None
        and application.salary_min > application.salary_max
    ):
        raise HTTPException(status_code=422, detail="salary_min cannot exceed salary_max")
    application.updated_at = datetime.now(UTC)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


@app.delete(
    "/api/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["applications"],
)
def delete_application(application_id: int, session: SessionDep) -> Response:
    application = get_application_or_404(application_id, session)
    session.delete(application)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/analytics", response_model=AnalyticsRead, tags=["analytics"])
def analytics(session: SessionDep) -> AnalyticsRead:
    rows = session.exec(
        select(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status)
    ).all()
    counts = {item.value: 0 for item in ApplicationStatus}
    counts.update({item.value: count for item, count in rows})
    total = sum(counts.values())
    responses = counts[ApplicationStatus.INTERVIEW] + counts[ApplicationStatus.OFFER]
    active = total - counts[ApplicationStatus.REJECTED]
    response_rate = round((responses / total) * 100, 1) if total else 0.0
    return AnalyticsRead(total=total, active=active, response_rate=response_rate, by_status=counts)
