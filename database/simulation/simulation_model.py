import uuid

from sqlalchemy import Column, UUID, Integer, ForeignKey
from sqlalchemy.orm import relationship

from database.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    day = Column(Integer)

    battery_reference = Column(UUID, ForeignKey("batteries.reference"))
    battery = relationship("Battery", back_populates="simulation")

    photovoltaic = relationship("Photovoltaic", back_populates="simulation")
    photovoltaic_reference = Column(UUID, ForeignKey("photovoltaics.reference"))

    weather_reference = Column(UUID, ForeignKey("weathers.reference"))
    weather = relationship("Weather", back_populates="simulation")

    energy_market_reference = Column(UUID, ForeignKey("energy_markets.reference"))
    energy_market = relationship("EnergyMarket", back_populates="simulation")

    schedule_reference = Column(UUID, ForeignKey("schedules.reference"))
    schedule = relationship("Schedule", back_populates="simulation")

    # weather = relationship("Weather", back_populates="simulation")
