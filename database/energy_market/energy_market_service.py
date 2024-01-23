import random
import uuid

from icecream import ic
from sqlalchemy.orm import Session

from database.weather.weather_service import get_weather_by_reference
from .energy_market_model import EnergyMarket

BASE_PRICE = 0.3


def get_energy_market_by_reference(db: Session, reference: uuid.UUID):
    return db.query(EnergyMarket).filter(EnergyMarket.reference == reference).first()


def calculate_energy_price(renewable_generation):
    merit_order_factor = 1 - 0.4 * renewable_generation
    energy_price = BASE_PRICE * merit_order_factor
    return energy_price


def create_price_for_day(db: Session, day: int, weather_reference: uuid.UUID):
    price_for_day = {}
    avg_price = 0

    spring_start = 80
    summer_start = 172
    autumn_start = 264

    if spring_start <= day < summer_start:
        renewable_generation_range = (0.75, 2.5)  # Adjusted range for spring
    elif summer_start <= day < autumn_start:
        renewable_generation_range = (1, 3.0)  # Adjusted range for summer
    else:
        renewable_generation_range = (0.25, 1.85)

    db_weather = get_weather_by_reference(db=db, reference=weather_reference)

    ic(db_weather.weather)

    for hour in range(24):
        sun_intensity = db_weather.weather.get(f"{hour}").get("sun")

        # renewable_generation_range = tuple(sun_intensity * value for value in (0.5, 2.5))
        renewable_generation_range_multi = (
            1 + sun_intensity * value if sun_intensity != 0 else value * 0.8
            for value in renewable_generation_range
        )

        renewable_generation = random.uniform(*renewable_generation_range_multi)

        # Calculate energy price based on the merit order simulation
        calculated_price = calculate_energy_price(renewable_generation)

        price_for_day[hour] = calculated_price
        avg_price += calculated_price

    db_energy_market = EnergyMarket(day=day, price=price_for_day)
    db.add(db_energy_market)
    db.commit()
    db.refresh(db_energy_market)
    return db_energy_market
