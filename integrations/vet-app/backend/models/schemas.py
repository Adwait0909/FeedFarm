from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Dict


class FacilityOut(BaseModel):
    id:            int
    name:          str
    facility_type: str
    district:      str
    taluka:        str
    address:       str
    latitude:      float
    longitude:     float
    department:    str
    contact:       str
    opening_hours: str
    distance_km:   Optional[float] = None

    model_config = {"from_attributes": True}


class NearbyRequest(BaseModel):
    latitude:  float = Field(..., ge=-90,  le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=25.0, ge=1,  le=200)
    limit:     int   = Field(default=10,   ge=1,  le=100)
    facility_type: Optional[str] = None

    @field_validator("latitude")
    @classmethod
    def validate_maharashtra_lat(cls, v):
        if not (15.0 <= v <= 23.0):
            raise ValueError("Latitude must be within Maharashtra (15°N–23°N)")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_maharashtra_lon(cls, v):
        if not (72.0 <= v <= 81.0):
            raise ValueError("Longitude must be within Maharashtra (72°E–81°E)")
        return v


class DistrictSearchRequest(BaseModel):
    district:      str
    taluka:        Optional[str] = None
    facility_type: Optional[str] = None
    limit:         int = Field(default=50, ge=1, le=200)


class ImportResponse(BaseModel):
    success:      bool
    message:      str
    inserted:     int
    skipped:      int
    total_parsed: int


class StatsResponse(BaseModel):
    total:   int
    by_type: Dict[str, int]


class NearbyResponse(BaseModel):
    count:      int
    facilities: List[FacilityOut]
    radius_km:  float
    latitude:   float
    longitude:  float


class DistrictResponse(BaseModel):
    count:      int
    district:   str
    taluka:     Optional[str]
    facilities: List[FacilityOut]
