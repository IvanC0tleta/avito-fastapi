from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas
import models
from database import get_db
from typing import List, Optional

router = APIRouter()

error_responses = {
    400: {
        "description": "Неверный формат запроса или его параметры.",
        "content": {
            "application/json": {
                "example": {"reason": "Неверный формат запроса или его параметры."}
            }
        }
    },
    401: {
        "description": "Пользователь не существует или некорректен.",
        "content": {
            "application/json": {
                "example": {"reason": "Пользователь не существует или некорректен."}
            }
        }
    },
    403: {
        "description": "Недостаточно прав для выполнения действия.",
        "content": {
            "application/json": {
                "example": {"reason": "Недостаточно прав для выполнения действия."}
            }
        }
    },
    404: {
        "description": "Тендер не найден.",
        "content": {
            "application/json": {
                "example": {"reason": "Тендер не найден."}
            }
        }
    }
}


@router.get("/", response_model=List[schemas.Tender],
            responses={
                400: error_responses[400]
            })
def get_tenders(limit: int = 5, offset: int = 0,
                service_type: Optional[models.TenderServiceType] = None,
                db: Session = Depends(get_db)):
    query = db.query(models.Tender)

    if service_type:
        query = query.filter(models.Tender.serviceType == service_type)

    response = query.limit(limit).offset(offset).all()

    return response


@router.post("/new", response_model=schemas.Tender,
             responses={
                 401: error_responses[401],
                 403: error_responses[403],
             })
def create_tender(tender: schemas.TenderCreate, db: Session = Depends(get_db)):
    user = get_user_by_username(tender.creatorUsername, db)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    check_organization_responsible(db, user_id=user.id, organization_id=tender.organizationId)

    db_tender = models.Tender(
        name=tender.name,
        description=tender.description,
        serviceType=tender.serviceType,
        organizationId=tender.organizationId
    )

    db.add(db_tender)
    db.commit()
    db.refresh(db_tender)

    add_tender_backup(db, db_tender)

    add_tender_user(db, tenderId=db_tender.id, userId=user.id)

    return db_tender


@router.get("/my", response_model=List[schemas.Tender],
            responses={
                401: error_responses[401]
            })
def get_user_tenders(username: str,
                     limit: int = 5, offset: int = 0,
                     db: Session = Depends(get_db)):
    user = get_user_by_username(username, db)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    tender_user = db.query(models.TenderUser).filter(
        models.TenderUser.userId == user.id
    ).all()

    tender_ids = [row.tenderId for row in tender_user]
    tenders = db.query(models.Tender).filter(models.Tender.id.in_(tender_ids))

    response = tenders.limit(limit).offset(offset).all()
    return response


@router.get("/{tenderId}/status",
            responses={
                401: error_responses[401],
                403: error_responses[403],
                404: error_responses[404]
            })
def get_tender_status(tenderId: str, username: str = "", db: Session = Depends(get_db)):
    tender = db.query(models.Tender).get(tenderId)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    user = get_user_by_username(username, db)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    check_organization_responsible(db, user_id=user.id, organization_id=tender.organizationId)
    return tender.status


@router.put("/{tenderId}/status", response_model=schemas.Tender,
            responses={
                400: error_responses[400],
                401: error_responses[401],
                403: error_responses[403],
                404: error_responses[404]
            })
def put_tender_status(tenderId: str, status: models.TenderStatus, username: str, db: Session = Depends(get_db)):
    tender = db.query(models.Tender).get(tenderId)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    if tender.status == models.TenderStatus.CREATED or tender.status == models.TenderStatus.CLOSED:
        user = get_user_by_username(username, db)
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

        check_organization_responsible(db, user_id=user.id, organization_id=tender.organizationId)

    tender.status = status
    db.add(tender)
    db.commit()
    db.refresh(tender)

    return tender


@router.patch("/{tenderId}/edit", response_model=schemas.Tender,
              responses={
                  400: {
                      "description": "Данные неправильно сформированы или не соответствуют требованиям.",
                      "content": {
                          "application/json": {
                              "example": {"reason": "Данные неправильно сформированы или не соответствуют требованиям."}
                          }
                      }
                  },
                  401: error_responses[401],
                  403: error_responses[403],
                  404: error_responses[404]
              })
def update_tender(tenderId: str, username: str, tender_update: schemas.TenderUpdate, db: Session = Depends(get_db)):
    db_tender = db.query(models.Tender).get(tenderId)
    if not db_tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    user = get_user_by_username(username, db)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    check_organization_responsible(db, user_id=user.id, organization_id=db_tender.organizationId)

    if tender_update.name is not None:
        db_tender.name = tender_update.name
    if tender_update.description is not None:
        db_tender.description = tender_update.description
    if tender_update.serviceType is not None:
        db_tender.serviceType = tender_update.serviceType

    db_tender.version += 1
    db.commit()
    db.refresh(db_tender)

    add_tender_backup(db, db_tender)

    return db_tender


@router.put("/{tenderId}/rollback/{version}", response_model=schemas.Tender,
            responses={
                400: error_responses[400],
                401: error_responses[401],
                403: error_responses[403],
                404: {
                    "description": "Тендер или версия не найдены.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Тендер или версия не найдены."}
                        }
                    }
                }
            })
def rollback_tender(tenderId: str, version: int, username: str, db: Session = Depends(get_db)):
    db_tender = db.query(models.Tender).get(tenderId)
    if not db_tender:
        raise HTTPException(status_code=404, detail="Тендер или версия не найдены.")

    user = get_user_by_username(username, db)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    check_organization_responsible(db, user_id=user.id, organization_id=db_tender.organizationId)

    db_tender_history = db.query(models.TenderVersion).filter(
        models.TenderVersion.tenderId == tenderId,
        models.TenderVersion.version == version
    ).first()

    if not db_tender_history:
        raise HTTPException(status_code=404, detail="Тендер или версия не найдены.")

    db_tender.name = db_tender_history.name
    db_tender.description = db_tender_history.description
    db_tender.serviceType = db_tender_history.serviceType
    db_tender.status = db_tender_history.status
    db_tender.version += 1

    db.commit()
    db.refresh(db_tender)

    add_tender_backup(db, db_tender)

    return db_tender


def check_organization_responsible(db: Session, user_id: str, organization_id: str):
    query = db.query(models.OrganizationResponsible).filter(
        models.OrganizationResponsible.organization_id == organization_id,
        models.OrganizationResponsible.user_id == user_id
    ).first()

    if not query:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия.")


def add_tender_backup(db: Session, tender: models.Tender):
    tender = models.TenderVersion(
        tenderId=tender.id,
        name=tender.name,
        description=tender.description,
        serviceType=tender.serviceType,
        status=tender.status,
        version=tender.version
    )

    db.add(tender)
    db.commit()
    db.refresh(tender)

    return tender


def add_tender_user(db: Session, tenderId: models.Tender.id, userId: models.Employee.id):
    db_tender_user = models.TenderUser(
        tenderId=tenderId,
        userId=userId
    )
    db.add(db_tender_user)
    db.commit()
    db.refresh(db_tender_user)


def get_user_by_username(username: str, db: Session):
    return db.query(models.Employee).filter(
        models.Employee.username == username
    ).first()
