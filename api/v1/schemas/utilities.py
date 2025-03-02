from typing import List, Optional, Union
from pydantic import BaseModel, field_validator


class DownloadRequest(BaseModel):

    file_url: str


class TextTranslateRequest(BaseModel):

    text: str
    target_language: str
    

class FetchStockMediaRequest(BaseModel):
    
    query: Union [str, List[str]]
    media_type: str = 'stock images'
    # media_type: Optional[str] = 'stock images'
    
    @field_validator('query')
    def validate_query_length(cls, value):
        # Check if query is a string
        if isinstance(value, str):
            if len(value) > 100:
                raise ValueError('Query cannot be longer than 100 characters.')
            
        # Check if query is a list of strings
        elif isinstance(value, list):
            for query_item in value:
                if len(query_item) > 100:
                    raise ValueError('Each query in the list cannot be longer than 100 characters.')
                
        return value

    @field_validator("media_type")
    def check_media_type(cls, value):
        allowed_types = [
            "stock images",
            "stock videos", 
            "takling avatar",
            "ai images",
            "3d moving videos",
            "ai illustrations"
        ]
        
        if value not in allowed_types:
            raise ValueError(f"Invalid media type: {value}. Must be one of {', '.join(allowed_types)}.")
        
        return value
    