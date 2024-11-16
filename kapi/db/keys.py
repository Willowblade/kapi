import dataclasses
from typing import Optional

from kapi.db.db import supabase


@dataclasses.dataclass
class Key:
    room_number: str
    building_id: str
    type: str
    id: Optional[str] = ""

    def __post_init__(self):
        self.id = f"{self.building_id}-{self.room_number}-{self.type}"


def does_key_exist(key_id: str):
    key = supabase.table("keys").select("*").eq("id", key_id).execute()
    if len(key.data) == 0:
        return False
    return True


def add_key(key: Key):
    supabase.table("keys").insert([
        {
            "id": key.id,
            "building_id": key.building_id,
            "room_number": key.room_number,
            "type": key.type
        }
    ]).execute()

    return key
