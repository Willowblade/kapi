import dataclasses
import uuid
from typing import Optional
from uuid import uuid5

from kapi.db.db import supabase

BORROWER_UUID5_NAMESPACE = uuid.UUID("50ad06e6-5abe-48d2-8912-148077032ae0")


@dataclasses.dataclass
class Borrower:
    name: str
    type: str
    company: Optional[str] = ""
    id: Optional[str] = ""

    def id_hash_string(self):
        if self.company is None:
            return f"{self.name}-{self.type}"
        return f"{self.name}-{self.type}-{self.company}"

    def __post_init__(self):
        self.id = str(uuid5(BORROWER_UUID5_NAMESPACE, self.id_hash_string()))


def does_borrower_exist(borrower_id: str):
    borrower = supabase.table("borrowers").select("*").eq("id", borrower_id).execute()
    if len(borrower.data) == 0:
        return False
    return True


def add_borrower(borrower: Borrower):
    supabase.table("borrowers").insert([
        {
            "id": borrower.id,
            "name": borrower.name,
            "company": borrower.company,
            "type": borrower.type
        }
    ]).execute()

    return borrower
