import uuid

from sqlalchemy import Column, UUID, Integer, JSON
from sqlalchemy.orm import relationship

from database.database import Base


class Weather(Base):
    __tablename__ = "weathers"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    day = Column(Integer)
    weather = Column(JSON)

    simulation = relationship("Simulation", back_populates="weather")
    # simulation_reference = Column(UUID, ForeignKey("simulations.reference"))
