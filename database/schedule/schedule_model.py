import uuid

from sqlalchemy import Column, UUID, Integer, ForeignKey, Float, JSON
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
    heat_factor = Column(Float)
    solution = Column(JSON)
    complete = Column(JSON)

    simulation = relationship("Simulation", back_populates="schedule")
    # simulation_reference = Column(UUID, ForeignKey("simulations.reference"))

    devices = relationship("Device", back_populates="schedule")
