import logging
import uuid

from icecream import ic
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from database.battery.battery_service import get_battery_by_reference
from database.database import engine
from database.device.device_model import BaseDevice
from database.energy_market.energy_market_service import get_energy_market_by_reference
from database.photovoltaic.photovoltaic_service import get_pv_output_by_reference
from database.schedule.schedule_service import (
    get_schedule_by_simulation,
    get_schedule_by_simulation_with_devices,
)
from database.simulation.simulation_model import Simulation
from database.weather.weather_model import Weather
from database.weather.weather_service import get_weather_by_reference


# TODO: add consumers or controllable devices that need to be used, but time can vary (e.g washing machine, dishwasher, etc.)
# these devices should have a latest time_slot


def calculate_solution(db: Session, simulation_reference: uuid.UUID):
    simulation = (
        db.query(Simulation)
        .filter(Simulation.reference == simulation_reference)
        .first()
    )
    # get pv output
    pv_output = get_pv_output_by_reference(
        db=db,
        photovoltaic_reference=simulation.photovoltaic_reference,
        day=simulation.day,
    )
    # get market price
    market_price = get_energy_market_by_reference(
        db=db, reference=simulation.energy_market_reference
    )
    # get battery
    battery = get_battery_by_reference(
        db=db, battery_reference=simulation.battery_reference
    )
    current_storage = battery.capacity * battery.charge
    # get weather
    weather = get_weather_by_reference(db=db, reference=simulation.weather_reference)
    # get schedule
    schedule = get_schedule_by_simulation_with_devices(
        db=db, simulation_reference=simulation_reference, day=simulation.day
    )

    solutionSchedule = {}

    heat_factor = schedule.heat_factor

    for hour in range(24):
        temp_solution = {}
        heat_factor -= TEMPERATURE_DIFF_FACTOR
        found_device = [
            device for device in schedule.devices if device.time_slot == hour
        ]
        usage_hour = sum(
            (device.base_device.wattage / 1000) * (device.duration / 60)
            for device in found_device
        )
        # print(hour, usage_hour)
        pv_output_hour = pv_output.energy.get(str(hour))
        energy = pv_output_hour - usage_hour
        new_heat_factor, device, energy_used = test_large_consumers(
            energy, hour, heat_factor
        )
        temp_solution.update(device)
        energy = energy_used

        print(hour, energy)
        print(heat_factor)
        logger.info(temp_solution)
        if energy > 0:
            # if pv output is greater than usage, charge battery
            charge, remaining_unused = charge_battery(
                current_storage, energy, battery.capacity
            )
            current_storage = charge
            used_for_battery = energy - remaining_unused
            if used_for_battery > 0:
                temp_solution["battery"] = {
                    "duration": 60,
                    "usage": used_for_battery,
                }

            if remaining_unused > 0:
                # Sell remaining energy for now
                temp_solution["market"] = {"duration": 60, "usage": remaining_unused}
        else:
            # if pv output is less than usage, discharge battery
            charge, remaining_unused = discharge_battery(current_storage, energy)
            current_storage = charge
        heat_factor = new_heat_factor
        solutionSchedule[hour] = temp_solution

    return solutionSchedule


def discharge_battery(charge, discharge_amount):
    if charge >= abs(discharge_amount):
        # Update the remaining charge of the battery
        charge -= abs(discharge_amount)
        remaining_unused = 0
    else:
        # If not enough charge, set the remaining charge to 0
        remaining_unused = abs(discharge_amount) - charge
        charge = 0
        return charge, remaining_unused
    return charge, remaining_unused


def charge_battery(charge, charge_amount, capacity):
    remaining_capacity = capacity - charge

    # Check if the charging amount exceeds the remaining capacity
    if charge_amount > remaining_capacity:
        # Calculate the excess charging amount
        excess_charge = charge_amount - remaining_capacity

        # Charge the battery to its full capacity
        charge = capacity

        return charge, excess_charge
    else:
        return charge + charge_amount, 0
        # Charge the battery within its remaining capacity
        # return self.update_charge(charge_amount)


TEMP_FACTOR = 1
TEMPERATURE_DIFF_FACTOR = 0.01
TEMP_LOWER_LIMIT = 0.4
TEMP_UPPER_LIMIT = 1.8

HEAT_PUMP_EFFICIENCY = 0.2


def use_heat_pump(current_heat_factor, energy, heatpump_wattage):
    # if tempfactor is below lower limit use heat pump
    mode = 1
    if current_heat_factor < TEMP_LOWER_LIMIT:
        # use heat pump based on energy choose mode
        if energy == 0:
            mode = 0.5
        elif energy > 0:
            mode = 0.75

        return HEAT_PUMP_EFFICIENCY * mode, heatpump_wattage * mode

    # if tempfactor is above upper limit dont use heat pump
    if current_heat_factor > TEMP_UPPER_LIMIT:
        return None, None
    # if tempfactor is between lower and upper limit use heat pump with efficiency
    if TEMP_LOWER_LIMIT < current_heat_factor < TEMP_UPPER_LIMIT:
        # choose mode based on current heat factor and energy
        mode = 1
        if energy >= heatpump_wattage:
            mode = 1
        elif energy >= heatpump_wattage / 2:
            mode = 0.5
        elif energy < heatpump_wattage / 4:
            return None, None, None

        while HEAT_PUMP_EFFICIENCY * mode + current_heat_factor > TEMP_UPPER_LIMIT:
            mode -= 0.25

        if heatpump_wattage * mode > energy:
            return None, None, None

    return HEAT_PUMP_EFFICIENCY * mode, heatpump_wattage * mode, mode


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def calculate_hourly_usage(devices):
    return sum(device.base_device.wattage / 1000 for device in devices)


def test_large_consumers(remaining_energy, hour, heat_factor):
    large_consumers = get_large_consumers()
    heatpump = filter(lambda device: device.type == "heat-pump", large_consumers)
    heatpump = list(heatpump)[0]

    wallbox = filter(lambda device: device.type == "wallbox", large_consumers)
    wallbox = list(wallbox)[0]

    heat_change = 0
    device = {}
    energy_usage = 0

    if heat_factor < 1.5:
        logger.info("Use heat pump")
        heat, wattage, duration = use_heat_pump(
            heat_factor, remaining_energy, heatpump.wattage / 1000
        )
        if heat:
            heat_change = heat
            logger.info(f"HEAT: {heat}")
            logger.info(f"WATTAGE: {wattage}")
            device["heatpump"] = {"duration": duration * 60, "usage": wattage}
            energy_usage += wattage
    if hour <= 6 or hour >= 20:
        logger.info("Use wallbox")

    return heat_factor + heat_change, device, remaining_energy - energy_usage


def use_large_consumers(heat_factor, unused_energy):
    logger.info("Use large consumers")
    large_consumers = get_large_consumers()
    heatpump = filter(lambda device: device.type == "heat-pump", large_consumers)
    heatpump = list(heatpump)[0]

    wallbox = filter(lambda device: device.type == "wallbox", large_consumers)
    wallbox = list(wallbox)[0]

    may_use_heatpump = (
        heat_factor < 1.5
    )  # TODO: may include hour on this condition and weather
    # which large consumer is useful?
    # use heat pump when heat factor is low
    if may_use_heatpump:
        heat_change, heatpump_usage = use_heat_pump(
            heat_factor, unused_energy, heatpump.wattage / 1000
        )
        heat_factor += heat_change
        unused_energy -= heatpump_usage

    # use wallbox when car charge is low
    # use charge battery when battery is low

    return heat_factor, unused_energy


def buy_from_market():
    logger.info("Buy from market")


Session = scoped_session(sessionmaker(bind=engine))


def get_large_consumers():
    with Session() as session:
        return session.query(BaseDevice).filter(BaseDevice.controllable == True).all()


def energy_manager(
    large_consumers,
    battery_storage,
    heat_factor,
    pv_output,
    market_price,
    schedule,
    battery_capacity,
):
    for hour in range(24):
        logger.info(f"HEAT: {hour}: {heat_factor}")
        logger.info(f"BATTERY: {hour}: {battery_storage}")
        found_device = [
            device for device in schedule.devices if device.time_slot == hour
        ]
        future_device = [
            device for device in schedule.devices if device.time_slot == hour + 1
        ]

        heat_factor -= TEMPERATURE_DIFF_FACTOR

        hourly_usage = calculate_hourly_usage(found_device)
        future_hourly_usage = calculate_hourly_usage(future_device)

        current_pv_output = pv_output.energy.get(str(hour))
        current_market_price = market_price.price.get(str(hour))
        future_pv_output = pv_output.energy.get(str(hour + 1))
        future_market_price = market_price.price.get(str(hour + 1))
        avg_price = sum(market_price.price.values()) / 24

        unused_energy = current_pv_output - hourly_usage

        if current_pv_output > hourly_usage:
            if future_pv_output > future_hourly_usage:
                heat_change, unused_energy = use_large_consumers(
                    heat_factor, unused_energy
                )
                heat_factor = heat_change

                if unused_energy > 0:
                    charge, remaining_unused = charge_battery(
                        battery_storage, unused_energy, battery_capacity
                    )
                    battery_storage = charge

                # charge, remaining_unused = charge_battery(
                #     battery_storage, current_pv_output - hourly_usage, battery_capacity
                # )
                # battery_storage = charge
            else:
                if current_market_price < avg_price:
                    logger.info(current_market_price)
                    heat_change, unused_energy = use_large_consumers(
                        heat_factor, unused_energy
                    )
                    heat_factor = heat_change

                charge, remaining_unused = charge_battery(
                    battery_storage, current_pv_output - hourly_usage, battery_capacity
                )
                battery_storage = charge

        elif current_pv_output < hourly_usage:
            if future_pv_output > future_hourly_usage:
                if current_market_price < avg_price:
                    # use_large_consumers()
                    logger.info(current_market_price)
                    logger.info("MAYBE Use large consumers")

                charge, remaining_unused = discharge_battery(
                    battery_storage, current_pv_output - hourly_usage
                )
                battery_storage = charge
            else:
                if current_market_price < avg_price:
                    buy_from_market()
                else:
                    charge, remaining_unused = discharge_battery(
                        battery_storage, current_pv_output - hourly_usage
                    )
                    battery_storage = charge

        elif current_market_price < avg_price:
            if current_pv_output > hourly_usage:
                charge, remaining_unused = charge_battery(
                    battery_storage, current_pv_output - hourly_usage, battery_capacity
                )
                battery_storage = charge
            else:
                logger.info(current_market_price)
                heat_change, unused_energy = use_large_consumers(
                    heat_factor, unused_energy
                )
                heat_factor = heat_change

        # get heat pump from large consumers
    # get wallbox from large consumers

    # if energy is positive thant there is unused energy:
    # if energy price is low use large consumers and charge battery
    # when heat factor is low use heat pump
    # when heat factor is high and wallbox is usable use wallbox
    # when battery is low charge battery
    # charge battery

    # if energy is negative than there is not enough energy

    # TODO return each hour with energy usage
    pass
