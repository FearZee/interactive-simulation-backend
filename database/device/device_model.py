import enum
import uuid

from sqlalchemy import Column, UUID, Integer, ForeignKey, Float, String, Enum
from sqlalchemy.orm import relationship

from database.database import Base


class BaseDevice(Base):
    __tablename__ = "base_devices"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )

    name = Column(String)
    type = Column(String)
    wattage = Column(Float)

    device = relationship("Device", back_populates="base_device")


class TypeEnum(enum.Enum):
    BASIC = "basic"
    CONTROLLABLE = "controllable"


class Device(Base):
    __tablename__ = "devices"

    reference = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    type = Column(Enum(TypeEnum))
    time_slot = Column(Integer)
    duration = Column(Integer)
    intensity = Column(Float, default=None)

    base_device = relationship("BaseDevice", back_populates="device")
    base_device_reference = Column(UUID, ForeignKey("base_devices.reference"))

    schedule = relationship("Schedule", back_populates="device")
    schedule_reference = Column(UUID, ForeignKey("schedules.reference"))
