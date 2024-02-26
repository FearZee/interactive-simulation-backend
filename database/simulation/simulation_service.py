import random
import uuid

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
from ..schedule.schedule_service import logic
from ..solution.solution_service import calculate_solution
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
    db_schedule = logic(db=db, simulation_reference=db_simulation.reference)
    db_simulation.schedule_reference = db_schedule.reference
    calculate_solution(db=db, simulation_reference=db_simulation.reference)
    db.commit()
    db.refresh(db_simulation)

    return db_simulation


def update_simulation(db: Session, simulation_reference: uuid.UUID):
    simulation = get_simulation_by_reference(
        db=db, simulation_reference=simulation_reference
    )
    day = random.randint(1, 365)
    simulation.day = day
    db.commit()
    db.refresh(simulation)
    db_weather = create_weather(db=db, day=day)
    simulation.weather_reference = db_weather.reference

    db_energy_market = create_price_for_day(
        db=db, day=day, weather_reference=db_weather.reference
    )
    simulation.energy_market_reference = db_energy_market.reference

    battery = create_battery(db, BatteryScheme(capacity=10, charge=0.2))
    simulation.battery_reference = battery.reference

    db_energy_out = calculate_solar_output_for_day(
        db=db,
        day=simulation.day,
        photovoltaic_reference=simulation.photovoltaic_reference,
    )
    db_schedule = logic(db=db, simulation_reference=simulation.reference)
    simulation.schedule_reference = db_schedule.reference
    calculate_solution(db=db, simulation_reference=simulation.reference)
    db.commit()
    db.refresh(simulation)
    return simulation


def get_complete_usage(db: Session, simulation_reference: uuid.UUID):
    simulation = get_simulation_by_reference(
        db=db, simulation_reference=simulation_reference
    )
    return simulation
