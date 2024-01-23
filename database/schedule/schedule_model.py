import uuid

from sqlalchemy import Column, UUID, Integer
from sqlalchemy.orm import relationship

from database.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    day = Column(Integer)

    # simulation = relationship("Simulation", back_populates="schedule")
    device = relationship("Device", back_populates="schedule")
