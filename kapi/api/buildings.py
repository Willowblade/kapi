import dataclasses

from fastapi import APIRouter, Query, Form
from starlette.responses import JSONResponse

from kapi.db.buildings import get_all_buildings, add_building

router = APIRouter()


@router.get("/")
async def get_all_buildings_endpoint(search: str = Query(None), limit: int = Query(20), offset: int = Query(0)):
    buildings, total = get_all_buildings(search=search, limit=limit, offset=offset)
    return JSONResponse(content={
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [dataclasses.asdict(building) for building in buildings],
    })


@router.post("/")
async def create_building(
        name: str = Form(...),
):
    return add_building(name)
