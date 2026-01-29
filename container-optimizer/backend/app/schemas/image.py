from pydantic import BaseModel
from typing import List

class ImageLayer(BaseModel):
    command: str
    size_mb: float
    is_large: bool

class ImageAnalysis(BaseModel):
    image: str
    total_size_mb: float
    layer_count: int
    base_image: str
    layers: List[ImageLayer]
