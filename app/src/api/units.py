from fastapi import APIRouter
from src.models.unit import Unit

router = APIRouter()

units = [
    {"id": "id_conc", "name": "concentration", "symbol": "#/cm3"},
    {"id": "id_temp", "name": "temperature", "symbol": "°C"},
]


@router.get("", response_model=list[Unit])
async def get_all():
    return units
