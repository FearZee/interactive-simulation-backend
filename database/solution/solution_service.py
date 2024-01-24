import uuid

from icecream import ic
from sqlalchemy.orm import Session

from database.battery.battery_service import get_battery_by_reference
from database.energy_market.energy_market_service import get_energy_market_by_reference
from database.photovoltaic.photovoltaic_service import get_pv_output_by_reference
from database.schedule.schedule_service import (
    get_schedule_by_simulation,
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

    # compare schedule hour with pv output hour
    for hour in range(24):
        found_device = [
            device for device in schedule.devices if device.time_slot == hour
        ]
        if not found_device:
            ic({f"{hour}": 0})
            continue

        hourly_usage = 0

        for device in found_device:
            hourly_usage += device.base_device.wattage

        pv_output_hourly = pv_output.energy.get(f"{hour}")
        market_price_hourly = market_price.price.get(f"{hour}")

        energy = pv_output_hourly - hourly_usage / 1000

        if energy > 0:
            # charge battery
            charge, remaining_unused = charge_battery(
                current_storage, energy, battery.capacity
            )
            current_storage = charge
            # think about what to do with energy
            pass
        else:
            battery_state = current_storage / battery.capacity
            if battery_state < 0.2:
                # buy from market
                ic({f"BUY FROM MARKET: {hour}": market_price_hourly})
                pass
            else:
                charge, remaining_unused = discharge_battery(current_storage, energy)
                current_storage = charge
                ic({f"USE BATTERY: {hour}": current_storage})
                ic({f"LEFT: {hour}": remaining_unused})

                # use battery
                pass
            # use battery or buy from market
            # if battery is empty buy from market
            # if battery is nearly full use it
            pass

        ic({f"USAGE: {hour}": hourly_usage})
        ic({f"PV: {hour}": pv_output_hourly})
        ic({f"MARKET PRICE: {hour}": market_price_hourly})

        # for device in found_device:
        #     ic(device.base_device.wattage)

        # usage = found_device.usage

        # if schedule.hour == pv_output.hour
        # calculate energy balance for each hour
        # do i need to discharge battery or buy from market
        # can i charge battery from pv or should i use large consumers?
        # use large consumers when energy price is low and needed
        # use battery when energy price is high and needed
        pass

    # calculate energy balance for each hour do i need to discharge battery or buy from market
    # can i charge battery from pv or should i use large consumers?
    # use large consumers when energy price is low and needed
    # use battery when energy price is high and needed

    pass


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
