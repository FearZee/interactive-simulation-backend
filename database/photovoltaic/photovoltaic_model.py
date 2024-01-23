import uuid

from sqlalchemy import Column, UUID, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from database.database import Base


class Photovoltaic(Base):
    __tablename__ = "photovoltaics"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    kilowatt_peak = Column(Float)

    energy_output = relationship("EnergyOutput", back_populates="photovoltaic")
    simulation = relationship("Simulation", back_populates="photovoltaic")


class EnergyOutput(Base):
    __tablename__ = "energy_outputs"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    day = Column(Integer)
    energy = Column(JSON)

    photovoltaic_reference = Column(UUID, ForeignKey("photovoltaics.reference"))
    photovoltaic = relationship("Photovoltaic", back_populates="energy_output")
