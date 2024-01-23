import uuid

from sqlalchemy import Column, UUID, Float
from sqlalchemy.orm import relationship

from database.database import Base


class Battery(Base):
    __tablename__ = "batteries"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    capacity = Column(Float)
    charge = Column(Float)

    simulation = relationship("Simulation", back_populates="battery")
