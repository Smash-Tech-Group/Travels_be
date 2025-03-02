from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel


class BasePresetModel(BaseTableModel):
    '''Base model for presets'''
    
    __abstract__ = True
    
    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)


class Voice(BasePresetModel):
    __tablename__ = "voices"
    
    name = Column(String, nullable=False)
    gender = Column(
        String,
        nullable=False,
        server_default='neutral'
    )
    
    avatars = relationship('Avatar', back_populates='voice')
    

class Avatar(BasePresetModel):
    __tablename__ = "avatars"
    
    # gender = Column(
    #     String,
    #     nullable=False,
    #     server_default='neutral'
    # )
    voice_id = Column(String, ForeignKey('voices.id', ondelete='CASCADE'),nullable=True)
    voice = relationship('Voice', back_populates='avatars')
    

class BackgroundMusic(BasePresetModel):
    __tablename__ = "background_music"
    

class BackgroundImage(BasePresetModel):
    __tablename__ = "background_images"
