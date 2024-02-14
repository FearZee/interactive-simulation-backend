import uuid

from sqlalchemy.orm import Session, scoped_session, sessionmaker

from database.battery.battery_service import get_battery_by_reference
from database.database import engine
from database.device.device_model import BaseDevice
from database.energy_market.energy_market_service import get_energy_market_by_reference
from database.photovoltaic.photovoltaic_service import get_pv_output_by_reference
from database.schedule.schedule_service import (
    get_schedule_by_simulation_with_devices,
)
from database.simulation.simulation_model import Simulation
from database.weather.weather_service import get_weather_by_reference


def calculate_solution(db: Session, simulation_reference: uuid.UUID):
    simulation = (
        db.query(Simulation)
        .filter(Simulation.reference == simulation_reference)
        .first()
    )

    pv_output = get_pv_output_by_reference(
        db=db,
        photovoltaic_reference=simulation.photovoltaic_reference,
        day=simulation.day,
    )

    market_price = get_energy_market_by_reference(
        db=db, reference=simulation.energy_market_reference
    )

    battery = get_battery_by_reference(
        db=db, battery_reference=simulation.battery_reference
    )
    current_storage = battery.capacity * battery.charge

    weather = get_weather_by_reference(db=db, reference=simulation.weather_reference)

    schedule = get_schedule_by_simulation_with_devices(
        db=db, simulation_reference=simulation_reference, day=simulation.day
    )

    solutionSchedule = {}

    heat_factor = schedule.heat_factor
    wanted_charge = 10

    complete_schedule = {}

    for hour in range(24):
        temp_solution = {}
        heat_factor -= TEMPERATURE_DIFF_FACTOR

        found_device = [
            device for device in schedule.devices if device.time_slot == hour
        ]

        temp_schedule = {}

        for d in found_device:
            temp_schedule[d.base_device.name] = {
                "duration": d.duration,
                "usage": d.base_device.wattage / 1000 * d.duration / 60,
            }
        complete_schedule[hour] = temp_schedule

        usage_hour = sum(
            (device.base_device.wattage / 1000) * (device.duration / 60)
            for device in found_device
        )

        pv_output_hour = pv_output.energy.get(str(hour))
        energy = pv_output_hour - usage_hour
        new_heat_factor, device, energy_used, car_charge = use_large_consumers(
            energy, hour, heat_factor, market_price.price, wanted_charge
        )
        temp_solution.update(device)
        energy = energy_used
        wanted_charge = car_charge

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

    merged_dict = recursive_merge(complete_schedule, solutionSchedule)

    schedule.solution = solutionSchedule
    schedule.complete = merged_dict
    db.commit()

    return solutionSchedule


def recursive_merge(dict1, dict2):
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if key in dict1 and isinstance(value, dict) and isinstance(dict1[key], dict):
            merged_dict[key] = recursive_merge(dict1[key], value)
        else:
            if (
                key in merged_dict
                and isinstance(merged_dict[key], dict)
                and isinstance(value, dict)
            ):
                merged_dict[key].update(value)
            else:
                merged_dict[key] = value
    return merged_dict


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


WALLBOX_MAX = 11


def use_wallbox(wanted_charge, energy, market_prices, wattage, hour):
    modes = [1, 0.75, 0.5, 0.25]
    if wanted_charge <= 0:
        return None, None, None

    if energy > 0:
        # use energy
        pass

    avg_market_price = sum(market_prices.values()) / len(market_prices)
    if market_prices.get(f"{hour}") < avg_market_price:
        if wanted_charge >= WALLBOX_MAX:
            # charge at max for full hour
            return WALLBOX_MAX, wattage, 60
        else:
            closest_mode = min(
                modes, key=lambda x: abs(WALLBOX_MAX * x - wanted_charge)
            )
            return WALLBOX_MAX * closest_mode, wattage * closest_mode, 60 * closest_mode

    return None, None, None


def calculate_hourly_usage(devices):
    return sum(device.base_device.wattage / 1000 for device in devices)


def use_large_consumers(
    remaining_energy, hour, heat_factor, market_price, wanted_charge
):
    large_consumers = get_large_consumers()
    heatpump = filter(lambda device: device.type == "heat-pump", large_consumers)
    heatpump = list(heatpump)[0]

    wallbox = filter(lambda device: device.type == "wallbox", large_consumers)
    wallbox = list(wallbox)[0]

    heat_change = 0
    device = {}
    energy_usage = 0

    if heat_factor < 1.5:
        heat, wattage, duration = use_heat_pump(
            heat_factor, remaining_energy, heatpump.wattage / 1000
        )
        if heat:
            heat_change = heat
            device["heatpump"] = {"duration": duration * 60, "usage": wattage}
            energy_usage += wattage
    if hour <= 6 or hour >= 20:
        car_charge, wattage, duration = use_wallbox(
            wanted_charge, remaining_energy, market_price, wallbox.wattage / 1000, hour
        )
        if car_charge:
            wanted_charge -= car_charge
            device["wallbox"] = {"duration": duration, "usage": wattage}

    return (
        heat_factor + heat_change,
        device,
        remaining_energy - energy_usage,
        wanted_charge,
    )


def buy_from_market():
    print("Buy from market")


Session = scoped_session(sessionmaker(bind=engine))


def get_large_consumers():
    with Session() as session:
        return session.query(BaseDevice).filter(BaseDevice.controllable == True).all()
