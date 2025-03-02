from fastapi import APIRouter, Depends, status, BackgroundTasks, Request, Query
from sqlalchemy.orm import Session
from api.db.database import get_db
from typing import Annotated
from api.core.responses import SUCCESS
from api.utils.pagination import paginated_response
from api.utils.success_response import success_response
from api.v1.services.contact_us import contact_us_service
from api.v1.services.email_sending import email_sending_service
from api.v1.schemas.contact_us import CreateContactUs
from fastapi.encoders import jsonable_encoder
from api.v1.services.user import user_service
from api.v1.models import *

contact_us = APIRouter(prefix="/contact", tags=["Contact Us"])


# CREATE
@contact_us.post(
    "",
    response_model=success_response,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Contact us message created successfully"},
        422: {"description": "Validation Error"},
    },
)
async def create_contact_us(
    request: Request,
    data: CreateContactUs, 
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Add a new contact us message."""
    new_contact_us_message = contact_us_service.create(db, schema=data)

    # Send email to admin
    email_sending_service.send_contact_us_success_email(
        request=request,
        background_tasks=background_tasks,
        contact_message=new_contact_us_message,
    )

    response = success_response(
        message='Message sent successfully',
        status_code=status.HTTP_201_CREATED,
        data=jsonable_encoder(new_contact_us_message)
    )
    return response


@contact_us.get(
    "",
    response_model=success_response,
    status_code=200,
    responses={
        403: {"description": "Unauthorized"},
        500: {"description": "Server Error"},
    },
)
def retrieve_contact_us(
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_super_admin),
    limit: int = Query(10),
    skip: int = Query(0)
):
    """
    Retrieve all contact-us submissions from database
    """

    return paginated_response(
        db=db,
        model=ContactUs,
        skip=skip,
        limit=limit
    )
