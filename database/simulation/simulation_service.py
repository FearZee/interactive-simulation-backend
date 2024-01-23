import random
import uuid

from icecream import ic
from sqlalchemy.orm import Session

from .simulation_model import Simulation
from ..battery.battery_scheme import BatteryScheme
from ..battery.battery_service import create_battery
from ..energy_market.energy_market_service import create_price_for_day
from ..photovoltaic.photovoltaic_scheme import CreatePhotovoltaicScheme
from ..photovoltaic.photovoltaic_service import (
    create_photovoltaic,
    calculate_solar_output_for_day,
)
from ..weather.weather_service import create_weather


def get_simulation_by_reference(db: Session, simulation_reference: uuid.UUID):
    return (
        db.query(Simulation)
        .filter(Simulation.reference == simulation_reference)
        .first()
    )


def create_simulation(db: Session):
    day = random.randint(1, 365)
    db_simulation = Simulation(day=day)
    db.add(db_simulation)
    db.commit()
    db.refresh(db_simulation)

    db_weather = create_weather(db=db, day=day)
    db_simulation.weather_reference = db_weather.reference

    db_energy_market = create_price_for_day(
        db=db, day=day, weather_reference=db_weather.reference
    )
    db_simulation.energy_market_reference = db_energy_market.reference

    db_photovoltaic = create_photovoltaic(db, CreatePhotovoltaicScheme(kilowatt_peak=5))
    db_simulation.photovoltaic_reference = db_photovoltaic.reference
    db.commit()
    db.refresh(db_simulation)

    battery = create_battery(db, BatteryScheme(capacity=10, charge=0.2))
    db_simulation.battery_reference = battery.reference

    db_energy_out = calculate_solar_output_for_day(
        db=db, day=db_simulation.day, photovoltaic_reference=db_photovoltaic.reference
    )

    return db_simulation
