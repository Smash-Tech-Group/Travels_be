from sqlalchemy import Column, String
from api.v1.models.base_model import BaseTableModel

class ContactUs(BaseTableModel):
    __tablename__ = 'contact_us'

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String(length=14), nullable=False)
    message = Column(String, nullable=False)
