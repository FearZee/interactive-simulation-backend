import uuid

from database.battery.battery_model import Battery
from database.battery.battery_scheme import BatteryScheme, UpdateBatteryScheme


def get_battery_by_reference(db, battery_reference: uuid.UUID):
    return db.query(Battery).filter(Battery.reference == battery_reference).first()


def create_battery(db, battery: BatteryScheme):
    db_battery = Battery(capacity=battery.capacity, charge=battery.charge)
    db.add(db_battery)
    db.commit()
    db.refresh(db_battery)
    return db_battery


def update_battery(db, battery_reference: uuid.UUID, battery: UpdateBatteryScheme):
    db_battery = get_battery_by_reference(db, battery_reference)
    db_battery.charge = battery.charge
    db.commit()
    db.refresh(db_battery)
    return db_battery
