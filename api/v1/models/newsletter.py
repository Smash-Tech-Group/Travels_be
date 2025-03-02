from sqlalchemy import Column, String, Text
from api.v1.models.base_model import BaseTableModel


class Newsletter(BaseTableModel):
    __tablename__ = "newsletters"

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    content = Column(Text, nullable=True)


class NewsletterSubscriber(BaseTableModel):
    __tablename__ = "newsletter_subscribers"

    email = Column(String, nullable=False)
