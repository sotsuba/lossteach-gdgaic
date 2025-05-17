from pydantic import BaseModel, Field
from typing import Annotated, Optional, List

class FragmentMetrics(BaseModel):
    area:        float = Field(0, description="Area of the fragment in pixels")
    perimeter:   float = Field(0, description="Perimeter of the fragment in pixels")
    circularity: float = Field(0, description="Circularity measure of the fragment")
    contour_count: Optional[int] = Field(0, description="Number of contours in the fragment")

class Fragment(BaseModel):
    id:         int = Field(..., description="Unique identifier for the fragment")
    bbox:       List[int] = Field(..., description="Bounding box coordinates [x1, y1, x2, y2]")
    score:      float = Field(..., description="Confidence score of the detection")
    size_cm:    float = Field(..., description="Size of the fragment in centimeters")
    mask_data:  Optional[List[int]] = Field(None, description="Compressed binary mask data (only included if requested)")
    metrics:    Optional[FragmentMetrics] = Field(None, description="Metrics of the fragment (only included if requested)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "bbox": [100, 100, 200, 200],
                "score": 0.95,
                "size_cm": 5.0,
                "metrics": {
                    "area": 10000.0,
                    "perimeter": 400.0,
                    "circularity": 0.785,
                    "contour_count": 1
                }
            }
        }
