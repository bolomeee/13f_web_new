from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select, delete
from typing import List
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import create_db_and_tables, get_session
from app.models.filing import Filing, FilingCreate, FilingRead
from app.services.edgar_service import edgar_service
from app.api import data_display

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

app.include_router(data_display.router, prefix="/api/data", tags=["data"])


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# --- Page Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "13F 数据管理系统"}
    )


@app.get("/data", response_class=HTMLResponse)
async def read_data_display(request: Request):
    return templates.TemplateResponse(
        "data_display.html", {"request": request, "title": "13F 数据展示"}
    )


# --- API Routes ---
@app.post("/api/filings", response_model=FilingRead)
async def create_filing_task(
    filing_data: FilingCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    # 1. Create DB Record
    db_filing = Filing.from_orm(filing_data)
    session.add(db_filing)
    session.commit()
    session.refresh(db_filing)

    # 2. Trigger Background Task
    background_tasks.add_task(edgar_service.process_filing_task, db_filing.id, session)

    return db_filing


@app.get("/api/filings", response_model=List[FilingRead])
async def read_filings(session: Session = Depends(get_session)):
    filings = session.exec(select(Filing).order_by(Filing.created_at.desc())).all()
    return filings


class DeleteRequest(BaseModel):
    ids: List[int]


@app.post("/api/filings/batch-delete")
async def delete_filings(
    delete_req: DeleteRequest, session: Session = Depends(get_session)
):
    statement = delete(Filing).where(Filing.id.in_(delete_req.ids))
    session.exec(statement)
    session.commit()
    return {"ok": True, "deleted_count": len(delete_req.ids)}
