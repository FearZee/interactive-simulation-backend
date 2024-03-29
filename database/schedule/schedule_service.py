import json
import uuid

from sqlalchemy.orm import Session, joinedload

from database.device.device_model import TypeEnum, Device
from database.device.device_scheme import CreateDeviceScheme
from database.device.device_service import create_device
from database.schedule.schedule_model import Schedule
from database.simulation.simulation_model import Simulation


def create_schedule(db: Session, day: int, heat_factor: float = 0.8):
    db_schedule = Schedule(day=day, heat_factor=heat_factor)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def get_schedule_by_reference(db: Session, schedule_reference):
    return db.query(Schedule).filter(Schedule.reference == schedule_reference).first()


def get_schedule_by_simulation(db: Session, simulation_reference: uuid.UUID, day: int):
    simulation = (
        db.query(Simulation)
        .filter(Simulation.reference == simulation_reference)
        .first()
    )
    return (
        db.query(Schedule)
        .filter(Schedule.reference == simulation.schedule_reference)
        .filter(Schedule.day == day)
        .first()
    )


def get_schedule_complete_by_simulation(
    db: Session, simulation_reference: uuid.UUID, day: int
):
    return (
        db.query(Schedule)
        .filter(Schedule.simulation_reference == simulation_reference)
        .filter(Schedule.day == day)
        .first()
        .complete
    )


def get_schedule_by_reference_with_devices(db: Session, schedule_reference):
    return (
        db.query(Schedule)
        .filter(Schedule.reference == schedule_reference)
        .options(joinedload(Schedule.devices).joinedload(Device.base_device))
        .first()
    )


def get_schedule_by_simulation_with_devices(db: Session, schedule_reference: uuid.UUID):
    return (
        db.query(Schedule)
        .filter(Schedule.reference == schedule_reference)
        .join(Device)
        .options(joinedload(Schedule.devices).joinedload(Device.base_device))
        .first()
    )


def get_schedule_with_usage(db: Session, schedule_reference: uuid):
    schedule_with_device = get_schedule_by_reference_with_devices(
        db, schedule_reference
    )
    return schedule_with_device


def logic(db: Session, simulation_reference: uuid.UUID):
    with open("example-data/example-schedule.json", "r") as json_file:
        example_schedule_data = json.load(json_file)

    simulation = (
        db.query(Simulation)
        .filter(Simulation.reference == simulation_reference)
        .first()
    )

    found_schedule = get_schedule_by_reference(
        db=db, schedule_reference=simulation.schedule_reference
    )

    if found_schedule:
        return found_schedule

    db_schedule = create_schedule(
        db=db,
        day=simulation.day,
        heat_factor=example_schedule_data.get("heatFactor"),
    )

    for schedule_hour in example_schedule_data.get("schedule").items():
        key, data = schedule_hour

        for device in data.get("devices"):
            create_device(
                db=db,
                device=CreateDeviceScheme(
                    device_type=TypeEnum.BASIC,
                    time_slot=key,
                    duration=device.get("duration"),
                    base_device_reference=device.get("base_device_reference"),
                    schedule_reference=db_schedule.reference,
                ),
            )
        # pass
        # ic(schedule_hour)

    db.commit()
    db.refresh(db_schedule)

    return db_schedule
