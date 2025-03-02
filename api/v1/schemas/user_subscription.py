from pydantic import BaseModel
from datetime import datetime
from typing import List

from api.v1.schemas.base_schema import ResponseBase, PaginationBase


class CreateUserSubSchema(BaseModel):
    user_id: str
    billing_plan_id: str
    start_date: datetime
    end_date: datetime


class CreateUserSubResponse(CreateUserSubSchema):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ViewUserSubReturnData(CreateUserSubResponse):
    is_active: bool
    user_name: str
    plan_name: str
    price: float
    currency: str


class UserSubscriptionListResponse(ResponseBase):
    user_subscriptions: List[ViewUserSubReturnData]
    pagination: PaginationBase
