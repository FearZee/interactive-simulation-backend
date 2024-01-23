import uuid

from sqlalchemy.orm import Session

from database.device.device_scheme import UpdateDeviceScheme, CreateBaseDevice
from device_model import Device, BaseDevice


def get_device_by_reference(db: Session, device_reference: uuid.UUID):
    return db.query(Device).filter(Device.reference == device_reference).first()


def update_device(db: Session, device_reference, update: UpdateDeviceScheme):
    db_device = (
        db.query(Device)
        .filter(Device.reference == device_reference)
        .filter(Device.type == "controllable")
        .first()
    )
    db_device.time_slot = update.get("timeSlot")
    db_device.duration = update.get("duration")
    db_device.intensity = update.get("intensity")
    db.commit()
    db.refresh(db_device)
    return db_device


def create_base_device(db: Session, device: CreateBaseDevice):
    db_base_device = BaseDevice(
        name=device.name,
        type=device.type,
        wattage=device.wattage,
    )
    db.add(db_base_device)
    db.commit()
    db.refresh(db_base_device)
    return db_base_device
