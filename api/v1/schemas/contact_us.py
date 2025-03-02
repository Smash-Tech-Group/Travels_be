from pydantic import BaseModel, EmailStr


class CreateContactUs(BaseModel):
    """Validate the contact us form data."""

    name: str
    email: EmailStr
    phone_number: str
    message: str
