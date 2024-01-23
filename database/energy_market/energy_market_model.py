import uuid

from sqlalchemy import Column, UUID, JSON, Integer
from sqlalchemy.orm import relationship

from database.database import Base


class EnergyMarket(Base):
    __tablename__ = "energy_markets"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    price = Column(JSON)
    day = Column(Integer)

    simulation = relationship("Simulation", back_populates="energy_market")
