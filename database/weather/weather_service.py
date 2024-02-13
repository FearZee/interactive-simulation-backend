import math

import random

import uuid

from sqlalchemy.orm import Session

from .solar_angle import calculate_solar_angle
from .weather_model import Weather

WIND_AMPLITUDE = 5
WIND_PERIOD = 24
LINEAR_TREND_SLOPE = 0.2
MAX_CLOUD_COVER = 0.8


def get_weather_by_simulation(db: Session, simulation_id: uuid.UUID):
    return db.query(Weather).filter(Weather.simulation_id == simulation_id).all()


def get_weather_by_reference(db: Session, reference: uuid.UUID):
    return db.query(Weather).filter(Weather.reference == reference).first()


def create_weather(db: Session, day: int):
    weather = {}
    for hour in range(24):
        (wind_speed, _) = simulate_hourly_weather(hour, day)
        cloud_cover = calculate_cloud_cover(
            weather[hour - 1]["cloud"] if hour > 0 else None
        )
        sun = get_sunlight_intensity(hour, day, cloud_cover)
        temperature = calculate_temperature_hourly(
            day, sun, (weather[hour - 1]["temperature"] if hour > 0 else None)
        )
        weather[hour] = {
            "wind": wind_speed,
            "sun": sun,
            "cloud": cloud_cover,
            "temperature": temperature,
        }
    db_weather = Weather(day=day, weather=weather)
    db.add(db_weather)
    db.commit()
    db.refresh(db_weather)
    return db_weather


def simulate_hourly_weather(hour: int, day: int = 1):
    sinusoidal_variation = WIND_AMPLITUDE * math.sin(2 * math.pi * hour / WIND_PERIOD)
    linear_trend = random.uniform(-LINEAR_TREND_SLOPE, LINEAR_TREND_SLOPE) * hour
    stable_period_variation = random.uniform(
        -1, 1
    )  # Small random variations during stable periods

    # Combining the components to determine wind speed
    wind_speed = max(
        0,
        min(
            1, abs((sinusoidal_variation + linear_trend + stable_period_variation) / 3)
        ),
    )

    return wind_speed, random.uniform(0, MAX_CLOUD_COVER)


def calculate_cloud_cover(previous_cloud_cover):
    previous_cloud_cover = (
        previous_cloud_cover
        if previous_cloud_cover is not None
        else random.uniform(0, 1) * MAX_CLOUD_COVER
    )
    new_cloud_cover = 0.2 * previous_cloud_cover + 0.8 * random.uniform(0, 1)
    return max(0, min(1, new_cloud_cover))


def get_sunlight_intensity(hour, day, cloud_cover):
    # Get the solar elevation angle from the Photovoltaic class
    solar_elevation_angle = calculate_solar_angle(hour, day)

    # Adjust sunlight intensity based on the solar elevation angle
    solar_elevation_factor = math.sin(math.radians(solar_elevation_angle))
    adjusted_intensity = solar_elevation_factor * (1 - cloud_cover)

    return max(0, min(1, adjusted_intensity))


def calculate_temperature_hourly(
    day: int, sun_intensity: int, prev_temperature: float | None
):
    season = get_season(day)

    temperature = (
        prev_temperature
        if prev_temperature is not None
        else generate_daily_average_temperature(season)
    )

    # Generate a random temperature variation within a small range
    temperature_variation = random.uniform(1, -1)

    # Adjust the temperature based on sun intensity
    adjusted_temperature = temperature + temperature_variation * (
        sun_intensity if sun_intensity > 0 else 1
    )

    # print(adjusted_temperature)
    #
    # # Ensure the temperature change is gradual from the previous temperature
    # min_change, max_change = -0.5, 0.5
    # temperature_change = random.uniform(min_change, max_change)
    # if prev_temperature is None:
    #     new_temperature = adjusted_temperature
    # else:
    #     new_temperature = max(
    #         min(prev_temperature + temperature_change, adjusted_temperature),  # 0.9
    #         temperature - max_change,  # 10
    #     )

    return adjusted_temperature


def get_season(day_of_year):
    # Define the start day of each season
    spring_start = 80  # March 21st
    summer_start = 172  # June 21st
    fall_start = 264  # September 21st
    winter_start = 355  # December 21st

    if spring_start <= day_of_year < summer_start:
        return "spring"
    elif summer_start <= day_of_year < fall_start:
        return "summer"
    elif fall_start <= day_of_year < winter_start:
        return "fall"
    else:
        return "winter"


def generate_daily_average_temperature(season):
    # Define temperature ranges for each season
    season_temps = {
        "spring": (15, 25),
        "summer": (25, 35),
        "fall": (10, 20),
        "winter": (-5, 5),
    }

    min_temp, max_temp = season_temps.get(season, (20, 30))
    return random.uniform(min_temp, max_temp)
