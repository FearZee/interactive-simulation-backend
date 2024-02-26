import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database.schedule.schedule_service import (
    get_schedule_by_simulation,
    get_schedule_complete_by_simulation,
)
from database.simulation.simulation_scheme import SimulationResponseScheme
from database.simulation.simulation_service import (
    get_simulation_by_reference,
    create_simulation,
)
from database.solution.generate_tips import generate_tips
from database.solution.solution_service import calculate_solution
from routes.get_db import get_db

simulation_router = APIRouter()


@simulation_router.get("/simulation/{simulation_reference}")
async def get_simulation(simulation_reference: uuid.UUID, db=Depends(get_db)):
    return get_simulation_by_reference(db=db, simulation_reference=simulation_reference)


@simulation_router.put("/simulation/", response_model=SimulationResponseScheme)
async def method_create_simulation(db=Depends(get_db)):
    return create_simulation(db=db)


@simulation_router.get("/simulation/{simulation_reference}/solution")
async def get_solution(simulation_reference: uuid.UUID, db=Depends(get_db)):
    return calculate_solution(db=db, simulation_reference=simulation_reference)


@simulation_router.get("/simulation/{simulation_reference}/{day}/complete_usage")
async def get_complete_usage(
    simulation_reference: uuid.UUID, day: int, db=Depends(get_db)
):
    return get_schedule_complete_by_simulation(
        db=db, simulation_reference=simulation_reference, day=day
    )


class UserDevice(BaseModel):
    name: str
    duration: int
    wattage: float
    base_device_reference: uuid.UUID


class Item(BaseModel):
    time_slot: int
    device: list[UserDevice]


@simulation_router.put("/simulation/{simulation_reference}/tips")
async def get_tip(
    simulation_reference: uuid.UUID, user_solution: list[Item], db=Depends(get_db)
):
    return generate_tips(
        db=db, simulation_reference=simulation_reference, user_solution=user_solution
    )
