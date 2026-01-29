from pydantic import BaseModel

class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    image_size_mb: float
    memory_usage_mb: float
