import dataclasses
import uuid
from typing import Optional, Tuple
from uuid import uuid5

from postgrest.types import CountMethod

from kapi.db.db import supabase

BUILDING_UUID5_NAMESPACE = uuid.UUID("50ad06e6-5abe-48d2-8912-148077032aee")


@dataclasses.dataclass
class Building:
    name: str
    id: Optional[str] = ""

    def __post_init__(self):
        if self.id == "":
            self.id = str(uuid5(BUILDING_UUID5_NAMESPACE, self.name))


def does_building_exist(building_name: str):
    building = supabase.table("buildings").select("*").eq("name", building_name).execute()
    if len(building.data) == 0:
        return False
    return True

def get_all_buildings(limit: int = 20, offset: int=0, search: str = None) -> Tuple[list[Building], int]:
    query = supabase.table("buildings").select("*", count=CountMethod.exact)
    if search is not None:
        query = query.ilike("name", f"%{search}%")
    buildings = query.limit(limit).offset(offset).execute()
    return [Building(building["name"], id=building["id"]) for building in buildings.data], buildings.count


def add_building(name: str):
    if does_building_exist(name):
        raise ValueError("Building already exists")

    building = Building(name)
    supabase.table("buildings").insert([
        {
            "id": building.id,
            "name": building.name
        }
    ]).execute()
    return building
