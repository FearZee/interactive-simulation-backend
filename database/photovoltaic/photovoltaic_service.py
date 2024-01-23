import math
import uuid

from icecream import ic
from sqlalchemy.orm import joinedload

from database.weather.weather_model import Weather
from .photovoltaic_model import Photovoltaic, EnergyOutput
from .photovoltaic_scheme import CreatePhotovoltaicScheme
from ..simulation.simulation_model import Simulation


def create_photovoltaic(db, photovoltaic: CreatePhotovoltaicScheme):
    db_photovoltaic = Photovoltaic(kilowatt_peak=photovoltaic.kilowatt_peak)
    db.add(db_photovoltaic)
    db.commit()
    db.refresh(db_photovoltaic)
    return db_photovoltaic


def get_output_by_day(db, day: int, photovoltaic_reference: uuid.UUID):
    output = (
        db.query(EnergyOutput)
        .filter(EnergyOutput.day == day)
        .filter(EnergyOutput.photovoltaic_reference == photovoltaic_reference)
        .all()
    )

    if len(output) == 0:
        calculate_solar_output_for_day(
            db=db, day=day, photovoltaic_reference=photovoltaic_reference
        )
        return (
            db.query(EnergyOutput)
            .filter(EnergyOutput.day == day)
            .filter(EnergyOutput.photovoltaic_reference == photovoltaic_reference)
            .all()
        )
    else:
        return output


def calculate_solar_output_for_day(db, day: int, photovoltaic_reference: uuid.UUID):
    ic(photovoltaic_reference)
    db_photovoltaic = (
        db.query(Photovoltaic)
        .filter(Photovoltaic.reference == photovoltaic_reference)
        .options(joinedload(Photovoltaic.simulation))
        .first()
    )

    ic(db_photovoltaic)

    # db_energy_output = db.query(EnergyOutput).filter(EnergyOutput.day == day).all()
    db_weather = (
        db.query(Weather)
        .filter(Weather.reference == db_photovoltaic.simulation[0].weather_reference)
        .first()
    )

    energy_output = {}
    for hour in range(24):
        hourly_output = (
            db_photovoltaic.kilowatt_peak
            * db_weather.weather[f"{hour}"].get("cloud")
            * math.sin(math.radians(__calculate_solar_angle(day, hour, 52.5)))
        )
        hourly_output = hourly_output if hourly_output > 0 else 0
        energy_output[f"{hour}"] = hourly_output
        # energy_output.append(hourly_output)
        # energy_output_db = EnergyOutput(
        #     day=day,
        #     hour=hour,
        #     energy=hourly_output,
        #     photovoltaic_reference=photovoltaic_reference,
        # )

    energy_output_db = EnergyOutput(
        day=day,
        energy=energy_output,
        photovoltaic_reference=photovoltaic_reference,
    )
    db.add(energy_output_db)
    db.commit()
    return energy_output


def __calculate_solar_angle(day: int, time: int, latitude: float):
    # Formula to calculate solar declination angle
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day - 81)))

    # Hour angle calculation
    hour_angle = 15 * (time - 12)

    # Solar zenith angle calculation
    solar_zenith_angle = math.degrees(
        math.acos(
            math.sin(math.radians(declination)) * math.sin(math.radians(latitude))
            + math.cos(math.radians(declination))
            * math.cos(math.radians(latitude))
            * math.cos(math.radians(hour_angle))
        )
    )

    # Solar elevation angle
    solar_elevation_angle = 90 - solar_zenith_angle

    return solar_elevation_angle
