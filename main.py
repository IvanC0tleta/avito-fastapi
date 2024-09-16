from fastapi import FastAPI, Depends, HTTPException, Request
import models
import tenders
import bids
from database import engine
from sqlalchemy.orm import Session
from database import get_db
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"reason": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"reason": "Неверный формат запроса или его параметры."}
    )


app.include_router(tenders.router, prefix="/api/tenders")
app.include_router(bids.router, prefix="/api/bids")


@app.get("/api/ping")
def ping():
    return "ok"


@app.get("/api/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.Employee).all()


@app.get("/api/organizations")
def get_organizations(db: Session = Depends(get_db)):
    return db.query(models.Organization).all()


@app.get("/api/organization_responsibles")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.OrganizationResponsible).all()

@app.get("/table")
def get_users(db: Session = Depends(get_db)):
    return {
        "BidReview": [column.name for column in models.BidReview.__table__.columns],
        "BidDecisionUsers": [column.name for column in models.BidDecisionUsers.__table__.columns]
    }



