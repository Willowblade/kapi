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
    email: Optional[str] = None
    phone: Optional[str] = None

    def id_hash_string(self):
        s = f"{self.type}"
        if self.type == "company":
            s = f"{s}-{self.company}"
        if self.name:
            s = f"{s}-{self.name}"
        if self.email:
            s = f"{s}-{self.email}"
        if self.phone:
            s = f"{s}-{self.phone}"
        return s

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
            "type": borrower.type,
            "email": borrower.email,
            "phone": borrower.phone
        }
    ]).execute()

    return borrower
