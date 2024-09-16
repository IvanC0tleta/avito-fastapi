from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import schemas
import models
from database import get_db
from typing import List

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
        "description": "Предложение не найдено.",
        "content": {
            "application/json": {
                "example": {"reason": "Предложение не найдено."}
            }
        }
    }
}


@router.post("/new", response_model=schemas.Bid,
             responses={
                 401: error_responses[401],
                 403: error_responses[403],
                 404: {
                     "description": "Тендер не найден.",
                     "content": {
                         "application/json": {
                             "example": {"reason": "Тендер не найден."}
                         }
                     }
                 }
             })
def create_bid(bid: schemas.BidCreate, db: Session = Depends(get_db)):
    tender = db.query(models.Tender).get(bid.tenderId)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    if bid.authorType == models.BidAuthorType.ORGANIZATION:
        organization = db.query(models.Organization).get(bid.authorId)
        if not organization:
            raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")
    else:
        employee = db.query(models.Employee).filter(
            models.Employee.id == bid.authorId).first()
        if not employee:
            raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    if tender.status != models.TenderStatus.PUBLISHED:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия.")

    db_bid = models.Bid(
        name=bid.name,
        description=bid.description,
        status=models.BidStatus.CREATED,
        tenderId=bid.tenderId,
        authorType=bid.authorType,
        authorId=bid.authorId
    )

    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)

    add_bid_backup(db, db_bid)

    return db_bid


@router.get("/my", response_model=List[schemas.Bid],
            responses={
                401: error_responses[401]
            })
def get_employee_bids(username: str,
                      limit: int = 5, offset: int = 0,
                      db: Session = Depends(get_db)):
    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    db_bids = db.query(models.Bid).filter(models.Bid.authorId == user.id)
    response = db_bids.limit(limit).offset(offset).all()
    return response


@router.get("/{bidId}/status")
def get_bid_status(bidId: str, username: str, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).get(bidId)
    if not bid:
        raise HTTPException(status_code=404, detail="Предложение не найдено")

    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    if bid.authorId != user.id:
        check_organization_responsible(db, user_id=user.id,
                                       organization_id=bid.authorId)
    return bid.status


@router.put("/{bidId}/status", response_model=schemas.Bid,
            responses={
                401: error_responses[401],
                403: error_responses[403],
                404: {
                    "description": "Предложение не найдено.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Предложение не найдено."}
                        }
                    }
                }
            })
def put_bid_status(bidId: str, status: models.BidStatus, username: str, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).get(bidId)
    if not bid:
        raise HTTPException(status_code=404, detail="Предложение не найдено")

    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    if bid.authorId != user.id:
        check_organization_responsible(db, user_id=user.id,
                                       organization_id=bid.authorId)
    bid.status = status
    db.commit()
    db.refresh(bid)

    return bid


@router.get("/{tenderId}/list", response_model=List[schemas.Bid],
            responses={
                400: error_responses[400],
                401: error_responses[401],
                403: error_responses[403],
                404: {
                    "description": "Тендер или предложение не найдено.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Тендер или предложение не найдено."}
                        }
                    }
                }
            })
def get_bids_tender(tenderId: str, username: str,
                    limit: int = 5, offset: int = 0,
                    db: Session = Depends(get_db)):
    tender = db.query(models.Tender).get(tenderId)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер или предложение не найдено.")
    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    organization_responsible = check_organization_responsible(db, user_id=user.id,
                                                              organization_id=tender.organizationId)
    is_author = db.query(models.Bid).filter(
        models.Bid.tenderId == tenderId,
        models.Bid.authorId == user.id
    ).first()

    if not organization_responsible and not is_author:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия.")

    bids = db.query(models.Bid).filter(
        models.Bid.tenderId == tenderId
    ).order_by(models.Bid.name).limit(limit).offset(offset).all()

    if not bids:
        raise HTTPException(status_code=404, detail="Тендер или предложение не найдено.")

    return bids


@router.patch("/{bidId}/edit", response_model=schemas.Bid,
              responses={
                  400: error_responses[400],
                  401: error_responses[401],
                  403: error_responses[403],
                  404: error_responses[404]
              })
def update_bid(bidId: str, username: str, bid_update: schemas.BidUpdate, db: Session = Depends(get_db)):
    db_bid = db.query(models.Bid).get(bidId)
    if not db_bid:
        raise HTTPException(status_code=404, detail="Предложение не найдено.")
    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    if db_bid.authorId != user.id:
        organization = check_organization_responsible(db, user_id=user.id,
                                                      organization_id=db_bid.authorId)
        if not organization:
            raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия.")

    if bid_update.name is not None:
        db_bid.name = bid_update.name
    if bid_update.description is not None:
        db_bid.description = bid_update.description

    db_bid.version += 1
    db.commit()
    db.refresh(db_bid)

    add_bid_backup(db, db_bid)

    return db_bid


@router.put("/{bidId}/rollback/{version}", response_model=schemas.Bid,
            responses={
                400: error_responses[400],
                401: error_responses[401],
                403: error_responses[403],
                404: {
                    "description": "Предложение или версия не найдены.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Предложение или версия не найдены."}
                        }
                    }
                }
            })
def rollback_bid(bidId: str, version: int, username: str, db: Session = Depends(get_db)):
    db_bid = db.query(models.Bid).get(bidId)
    if not db_bid:
        raise HTTPException(status_code=400, detail="Предложение или версия не найдены.")

    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    if db_bid.authorId != user.id:
        organization = check_organization_responsible(db, user_id=user.id,
                                                      organization_id=db_bid.authorId)
        if not organization:
            raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия.")

    db_bid_history = db.query(models.BidVersion).filter(
        models.BidVersion.bidId == bidId,
        models.BidVersion.version == version
    ).first()

    if not db_bid_history:
        raise HTTPException(status_code=404, detail="Предложение или версия не найдены.")

    db_bid.name = db_bid_history.name
    db_bid.description = db_bid_history.description
    db_bid.status = db_bid_history.status
    db_bid.version += 1

    db.commit()
    db.refresh(db_bid)

    add_bid_backup(db, db_bid)

    return db_bid


@router.put("/{bidId}/submit_decision", response_model=schemas.Bid,
            responses={
                401: error_responses[401],
                403: error_responses[403],
                404: error_responses[404],
                400: {
                    "description": "Решение не может быть отправлено.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Решение не может быть отправлено."}
                        }
                    }
                }
            })
def submit_decision(bidId: str, decision: models.BibDecision, username: str, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).get(bidId)
    if not bid:
        raise HTTPException(status_code=404, detail="Предложение не найдено.")
    if bid.status == models.BidStatus.CANCELED:
        raise HTTPException(status_code=400, detail="Решение не может быть отправлено.")
    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    tender = db.query(models.Tender).get(bid.tenderId)
    check_organization_responsible(db, user_id=user.id, organization_id=tender.organizationId)

    db_decision = models.BidDecisionUsers(
        bidId=bidId,
        decision=decision,
        username=username
    )
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)

    if decision == models.BibDecision.REJECTED:
        bid.status = models.BidStatus.CANCELED
    else:
        current_quorum = len(db.query(models.BidDecisionUsers).filter(
            models.BidDecisionUsers.bidId == bidId).all())
        quorum = len(db.query(models.OrganizationResponsible).filter(
            models.OrganizationResponsible.organization_id == tender.organizationId
        ).all())
        if current_quorum >= min(3, quorum):
            tender.status = models.TenderStatus.CLOSED

    db.commit()
    db.refresh(bid)

    return bid


@router.put("/{bidId}/feedback", response_model=schemas.Bid,
            responses={
                401: error_responses[401],
                403: error_responses[403],
                404: error_responses[404],
                400: {
                    "description": "Отзыв не может быть отправлено.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Отзыв не может быть отправлено."}
                        }
                    }
                }
            })
def submit_review(bidId: str, bidFeedback: str, username: str, db: Session = Depends(get_db)):
    bid = db.query(models.Bid).get(bidId)
    if not bid:
        raise HTTPException(status_code=404, detail="Предложение не найдено.")
    user = db.query(models.Employee).filter(
        models.Employee.username == username).first()
    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не существует или некорректен.")
    tender = db.query(models.Tender).get(bid.tenderId)
    check_organization_responsible(db, user_id=user.id, organization_id=tender.organizationId)

    feedback = models.BidReview(
        bidAuthorId=bid.authorId,
        description=bidFeedback
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return bid


@router.get("/{tenderId}/reviews", response_model=list[schemas.BidReview],
            responses={
                400: error_responses[400],
                401: error_responses[401],
                403: error_responses[403],
                404: {
                    "description": "Тендер или отзывы не найдены.",
                    "content": {
                        "application/json": {
                            "example": {"reason": "Тендер или отзывы не найдены."}
                        }
                    }
                }
            })
def get_reviews(tenderId: str,
                authorUsername: str,
                requesterUsername: str,
                limit: int = 5, offset: int = 0,
                db: Session = Depends(get_db)):
    tender = db.query(models.Tender).get(tenderId)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер или отзывы не найдены")
    user_author = db.query(models.Employee).filter(
        models.Employee.username == authorUsername
    ).first()
    if not user_author:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")
    user_requester = db.query(models.Employee).filter(
        models.Employee.username == requesterUsername
    ).first()
    if not user_requester:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен.")

    check_organization_responsible(db, user_id=user_requester.id, organization_id=tender.organizationId)

    query_reviews = db.query(models.BidReview).filter(
        models.BidReview.bidAuthorId == user_author.id
    )

    reviews = query_reviews.limit(limit).offset(offset).all()

    if not reviews:
        raise HTTPException(status_code=404, detail="Тендер или отзывы не найдены")

    return reviews


def check_organization_responsible(db: Session, user_id: int, organization_id: int):
    query = db.query(models.OrganizationResponsible).filter(
        models.OrganizationResponsible.organization_id == organization_id,
        models.OrganizationResponsible.user_id == user_id
    ).first()

    if not query:
        raise HTTPException(status_code=400, detail="Недостаточно прав для выполнения действия.")

    return query


def add_bid_backup(db: Session, bid: models.Bid):
    bid = models.BidVersion(
        bidId=bid.id,
        name=bid.name,
        description=bid.description,
        status=bid.status,
        version=bid.version
    )

    db.add(bid)
    db.commit()
    db.refresh(bid)

    return bid
