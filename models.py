from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime, func
from database import Base
import enum
import uuid
from sqlalchemy.dialects.postgresql import UUID


class OrganizationType(str, enum.Enum):
    IE = 'IE'
    LLC = 'LLC'
    JSC = 'JSC'


class TenderStatus(str, enum.Enum):
    CREATED = 'Created'
    PUBLISHED = 'Published'
    CLOSED = 'Closed'


class TenderServiceType(str, enum.Enum):
    CONSTRUCTION = 'Construction'
    DELIVERY = 'Delivery'
    MANUFACTURE = 'Manufacture'


class BidStatus(str, enum.Enum):
    CREATED = 'Created'
    PUBLISHED = 'Published'
    CANCELED = 'Canceled'


class BidAuthorType(str, enum.Enum):
    ORGANIZATION = 'Organization'
    USER = 'User'


class BibDecision(str, enum.Enum):
    APPROVED = 'Approved'
    REJECTED = 'Rejected'


class Employee(Base):
    __tablename__ = "employee"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Organization(Base):
    __tablename__ = "organization"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(Enum(OrganizationType), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OrganizationResponsible(Base):
    __tablename__ = "organization_responsible"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    organization_id = Column(UUID, ForeignKey('organization.id', ondelete='CASCADE'))
    user_id = Column(UUID, ForeignKey('employee.id', ondelete='CASCADE'))


class Tender(Base):
    __tablename__ = "tender"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    name = Column(String(100))
    description = Column(String(500))
    serviceType = Column(Enum(TenderServiceType))
    status = Column(Enum(TenderStatus), default=TenderStatus.CREATED)
    organizationId = Column(UUID, ForeignKey("organization.id", ondelete='CASCADE'))
    version = Column(Integer, default=1)
    createdAt = Column(DateTime, server_default=func.now())


class Bid(Base):
    __tablename__ = 'bid'

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    name = Column(String(100))
    description = Column(String(500))
    status = Column(Enum(BidStatus), default=BidStatus.CREATED)
    tenderId = Column(UUID)
    authorType = Column(Enum(BidAuthorType))
    authorId = Column(UUID)
    version = Column(Integer, default=1)
    createdAt = Column(DateTime, server_default=func.now())


class TenderUser(Base):
    __tablename__ = "tender_user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    tenderId = Column(UUID, ForeignKey('tender.id', ondelete='CASCADE'))
    userId = Column(UUID, ForeignKey('employee.id', ondelete='CASCADE'))


class TenderVersion(Base):
    __tablename__ = "tenderVersion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    tenderId = Column(UUID, ForeignKey('tender.id', ondelete='CASCADE'))
    name = Column(String(100))
    description = Column(String(500))
    serviceType = Column(Enum(TenderServiceType))
    status = Column(Enum(TenderStatus))
    version = Column(Integer, default=1)


class BidVersion(Base):
    __tablename__ = 'bidVersion'

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    bidId = Column(UUID, ForeignKey('bid.id', ondelete='CASCADE'))
    name = Column(String(100))
    description = Column(String(500))
    status = Column(Enum(BidStatus), default=BidStatus.CREATED, nullable=False)
    version = Column(Integer, default=1)


class BidReview(Base):
    __tablename__ = 'bidReview'

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    bidAuthorId = Column(UUID)
    description = Column(String(1000))
    createdAt = Column(DateTime, server_default=func.now())


class BidDecisionUsers(Base):
    __tablename__ = 'BidDecisionUsers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.uuid_generate_v4())
    bidId = Column(UUID, ForeignKey('bid.id', ondelete='CASCADE'))
    decision = Column(Enum(BibDecision))
    username = Column(String(100))
