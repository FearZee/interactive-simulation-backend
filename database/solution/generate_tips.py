import uuid

from sqlalchemy.orm import Session

from database.device.device_model import BaseDevice
from database.schedule.schedule_model import Schedule
from database.simulation.simulation_model import Simulation
import numpy as np


def generate_tips(db: Session, simulation_reference: uuid.UUID, user_solution: list):
    simulation = (
        db.query(Simulation)
        .filter(Simulation.reference == simulation_reference)
        .first()
    )
    schedule = (
        db.query(Schedule)
        .filter(Schedule.reference == simulation.schedule_reference)
        .first()
    )

    # for hour in range(24):
    # compare user solution devices with solution devices
    # if user solution device is not in solution devices, check if there was unused energy
    # if there was unused energy, return well done
    # else return you could have saved energy
    # if user solution device is in solution devices return well done

    temp_tip = {}

    for hour in range(24):
        found_device = schedule.solution.get(str(hour))

        user_devices = np.array(
            [item.device for item in user_solution if item.time_slot == hour]
        ).flatten()

        devices = []

        for key, value in found_device.items():
            # TODO make this dry
            if key == "wallbox":
                device = (
                    db.query(BaseDevice).filter(BaseDevice.type == "wallbox").first()
                )
                devices.append(device)
            elif key == "heatpump":
                device = (
                    db.query(BaseDevice).filter(BaseDevice.type == "heat-pump").first()
                )
                devices.append(device)

            elif key == "battery":
                device = (
                    db.query(BaseDevice).filter(BaseDevice.type == "battery").first()
                )
                devices.append(device)

        temp = []
        for device in devices:
            for user_device in user_devices:
                print(user_device)
                if device.reference == user_device.base_device_reference:
                    print("Well done")
                    break
                else:
                    print("todo")
                    temp.append(
                        {"device": device, "messagee": "You could have used energy"}
                    )
                    # print("You could have used energy with", device)
                # if device.base_device_reference not in user_device:
                #     print("You could have saved energy")
            else:
                temp.append(
                    {"device": device, "messagee": "You could have used energy"}
                )

            temp_tip[hour] = {"devices": []}
            temp_tip[hour]["devices"] = temp
            break

        else:
            if user_devices:
                print("May save energy")
                pass
            else:
                temp_tip[hour] = {"message": "Good joob"}

    return temp_tip
