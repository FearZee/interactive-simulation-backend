import json

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware


from database.battery import battery_model
from database.database import engine, SessionLocal
from database.device import device_model
from database.device.device_model import BaseDevice
from database.energy_market import energy_market_model
from database.photovoltaic import photovoltaic_model
from database.schedule import schedule_model
from database.simulation import simulation_model
from database.weather import weather_model
from database.weather.weather_service import create_weather
from routes.schedule import schedule_router
from routes.simulation import simulation_router
from routes.photovoltaic import pv_router
from routes.weather import weather_router

simulation_model.Base.metadata.create_all(bind=engine)
weather_model.Base.metadata.create_all(bind=engine)
energy_market_model.Base.metadata.create_all(bind=engine)
schedule_model.Base.metadata.create_all(bind=engine)
device_model.Base.metadata.create_all(bind=engine)
photovoltaic_model.Base.metadata.create_all(bind=engine)
battery_model.Base.metadata.create_all(bind=engine)

app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://75.119.145.51:81",
    "http://bs.plaesh.de",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(simulation_router)
app.include_router(pv_router)
app.include_router(schedule_router)
app.include_router(weather_router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


all_devices = []


def init_db(db: Session):
    found_devices = db.query(BaseDevice).all()
    for device in all_devices:
        if not found_devices:
            db_device = BaseDevice(
                reference=device.get("reference"),
                name=device.get("name"),
                type=device.get("type"),
                wattage=device.get("wattage"),
                controllable=device.get("controllable"),
            )
            db.add(db_device)
            db.commit()
            db.refresh(db_device)


with open("example-data/base_devices.json", "r") as file:
    data = json.load(file)
    available_devices = data.get("base_devices")
    for device in available_devices:
        all_devices.append(device)


with Session(engine) as session:
    init_db(db=session)


@app.get("/")
async def root(db: Session = Depends(get_db)):
    return create_weather(db=db, day=23)


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
