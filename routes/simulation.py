import uuid

from fastapi import APIRouter, Depends

from database.simulation.simulation_scheme import SimulationResponseScheme
from database.simulation.simulation_service import (
    get_simulation_by_reference,
    create_simulation,
)
from routes.get_db import get_db

simulation_router = APIRouter()


@simulation_router.get("/simulation/{simulation_reference}")
async def get_simulation(simulation_reference: uuid.UUID, db=Depends(get_db)):
    return get_simulation_by_reference(db=db, simulation_reference=simulation_reference)


@simulation_router.put("/simulation/", response_model=SimulationResponseScheme)
async def method_create_simulation(db=Depends(get_db)):
    return create_simulation(db=db)