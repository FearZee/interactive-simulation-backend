import uuid

from pydantic import BaseModel

from database.device.device_model import TypeEnum


class DeviceScheme(BaseModel):
    reference: uuid.UUID
    device_type: str
    time_slot: int
    duration: int
    intensity: float

    base_device_reference: uuid.UUID
    schedule_reference: uuid.UUID

    class Config:
        from_attributes = True


class CreateDeviceScheme(BaseModel):
    device_type: TypeEnum
    time_slot: int
    duration: int
    intensity: float = None

    base_device_reference: uuid.UUID
    schedule_reference: uuid.UUID

    class Config:
        from_attributes = True


class UpdateDeviceScheme(BaseModel):
    timeSlot: int
    duration: int
    intensity: float


class BaseDeviceScheme(BaseModel):
    reference: uuid.UUID
    name: str
    type: str
    wattage: float

    class Config:
        from_attributes = True


class CreateBaseDevice(BaseModel):
    name: str
    type: str
    wattage: int

    class Config:
        from_attributes = True
