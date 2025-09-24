
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class PaymentStatus(str, Enum):
    unpaid = "unpaid"
    partial = "partial"
    paid = "paid"

class WorkStatus(str, Enum):
    draft = "draft"
    quoted = "quoted"
    accepted = "accepted"
    scheduled = "scheduled"
    in_progress = "in_progress"
    work_done = "work_done"
    closed = "closed"

class ClientIn(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class JobCreate(BaseModel):
    client_id: str
    title: str
    description: str = ""
    price_cents: int = Field(ge=0)
    status: str = "active"  # if you're still keeping your older status; or drop if migrating to work_status

class JobOut(BaseModel):
    id: str
    client_id: str
    title: str
    description: str
    price_cents: int
    amount_paid_cents: int
    payment_status: PaymentStatus
    work_status: WorkStatus
    created_at: Optional[str] = None
