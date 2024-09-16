from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

from models import TenderStatus, BidStatus, TenderServiceType, BidAuthorType


class TenderCreate(BaseModel):
    name: str
    description: str
    serviceType: TenderServiceType
    organizationId: str
    creatorUsername: str


class TenderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    serviceType: Optional[TenderServiceType] = None


class Tender(BaseModel):
    id: UUID
    name: str
    description: str
    status: TenderStatus
    serviceType: TenderServiceType
    version: int
    createdAt: datetime

    class Config:
        from_attributes = True


class BidCreate(BaseModel):
    name: str
    description: str
    tenderId: str
    authorType: BidAuthorType
    authorId: str


class BidUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Bid(BaseModel):
    id: UUID
    name: str
    status: BidStatus
    authorType: BidAuthorType
    authorId: UUID
    version: int
    createdAt: datetime

    class Config:
        from_attributes = True


class BidReview(BaseModel):
    id: UUID
    description: str
    createdAt: datetime

    class Config:
        from_attributes = True
