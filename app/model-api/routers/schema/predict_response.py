from pydantic import BaseModel
from typing import List
from routers.schema.fragment import Fragment
class SizeDistribution(BaseModel):
    bins:   list = []
    counts: list = []
    
class SizeMetrics(BaseModel):
    min_size:   float = 0.0
    max_size:   float = 0.0
    mean_size:  float = 0.0
    med_size:   float = 0.0
    std_size:   float = 0.0
    size_distribution: SizeDistribution

class PredictResponse(BaseModel):
    fragments: List[Fragment] = []
    size_mectrics: List[SizeMetrics] = []

