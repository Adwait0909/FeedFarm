from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base


class VeterinaryFacility(Base):
    __tablename__ = "veterinary_facilities"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name          = Column(String(500), nullable=False, index=True)
    facility_type = Column(String(100), nullable=False, index=True)
    district      = Column(String(200), nullable=True, index=True)
    taluka        = Column(String(200), nullable=True, index=True)
    address       = Column(String(1000), nullable=True)
    latitude      = Column(Float, nullable=False)
    longitude     = Column(Float, nullable=False)
    department    = Column(String(300), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Prevent duplicates on re-import
    __table_args__ = (
        UniqueConstraint("name", "latitude", "longitude", name="uq_facility_name_coords"),
    )

    def __repr__(self):
        return f"<VeterinaryFacility id={self.id} name={self.name!r} type={self.facility_type!r}>"
