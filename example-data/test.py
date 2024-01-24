import json
import random
from datetime import datetime
from pprint import pprint


def is_weekday(day_of_year):
    # Assuming day_of_year is 1-indexed (1 to 365/366)
    date_object = datetime.strptime(str(day_of_year), "%j")
    day_of_week = date_object.weekday()  # Monday is 0 and Sunday is 6

    # Check if it's a weekday (Monday to Friday)
    return day_of_week < 5


def generate_hourly_schedule(devices, preferred_schedules):
    schedule = {}

    for preferred_schedule in preferred_schedules:
        hour = preferred_schedule["hour"] % 24
        schedule[f"{hour}"] = []

        for device_type, data in preferred_schedule["deviceTypes"].items():
            devices_of_type = [
                device for device in devices if device["type"] == device_type
            ]

            if not devices_of_type:
                continue

            # calculate if device should be used
            should_use_device = random.random() < (
                data.get("use_factor")
                if is_weekday(255)
                else data.get("weekend_factor")
            )
            if not should_use_device:
                continue

            selected_devices = []
            # calculate how many devices should be used
            selected_devices.append(devices_of_type[0])

            for selected_device in selected_devices:
                print(selected_device)
                duration_factor = data.get("duration_factor")
                duration = preferred_schedule["duration"] * duration_factor

                schedule_entry = {
                    "deviceReference": selected_device["reference"],
                    "duration": duration * 60,
                }
                schedule.get(f"{hour}").append(schedule_entry)

    return schedule


# Load devices from the provided JSON
with open("example-data/base_devices.json", "r") as json_file:
    devices_data = json.load(json_file)

# Define preferred schedules with use factors and duration factors
preferred_schedules = [
    {
        "hour": 8,
        "duration": 1,
        "deviceTypes": {
            "coffee-machine": {
                "use_factor": 0.5,
                "weekend_factor": 0.5,
                "duration_factor": 5 / 60,
            },
            "toaster": {
                "use_factor": 0.8,
                "weekend_factor": 0.2,
                "duration_factor": 5 / 60,
            },
            "oven": {
                "use_factor": 0.2,
                "weekend_factor": 0.8,
                "duration_factor": 20 / 60,
            },
        },
    }
    # Add more schedules as needed
]

# Generate hourly schedule for the selected devices
devices_hourly_schedule = generate_hourly_schedule(
    devices=devices_data["base_devices"], preferred_schedules=preferred_schedules
)

# Print the generated schedule to the console
pprint({"schedule": devices_hourly_schedule}, indent=2)


print(is_weekday(255))
