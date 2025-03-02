from sqlalchemy import Column, String, Text, Float
from api.v1.models.base_model import BaseTableModel


class Testimonial(BaseTableModel):
    __tablename__ = 'testimonials'

    client_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Float, default=1, nullable=False)
    client_position = Column(String, nullable=False)
    avatar_url = Column(String)