import dataclasses
import datetime
import os
import uuid
from typing import Optional, Any, Self
from uuid import uuid4, uuid5

from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

print(f"Connecting to Supabase with {url=}, {key=}")

supabase: Client = create_client(url, key)

print(f"Connected to Supabase")



BORROWER_UUID5_NAMESPACE = uuid.UUID("50ad06e6-5abe-48d2-8912-148077032ae0")

# keys = supabase.table("keys").select("*").execute()
# borrowers = supabase.table("borrowers").select("*").execute()
# borrowed_keys = supabase.table("borrowed_keys").select("*").execute()
# print("Keys", keys)
# print("Borrowers", borrowers)
# print("Borrowed Keys", borrowed_keys)


@dataclasses.dataclass
class Key:
    number: str
    building: str
    room: str
    id: Optional[str] = ""

    def __post_init__(self):
        self.id = f"{self.building}-{self.room}-{self.number}"

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

@dataclasses.dataclass
class Files:
    image_filename: str
    signature_filename: str

@dataclasses.dataclass
class BorrowedKey:
    key: str # ID of the key
    borrowed_by: str # ID of the borrower
    image_filename: str
    signature_filename: str
    borrowed: Optional[bool] = True
    borrowed_at: Optional[str] = ""
    returned_at: Optional[str] = ""

    id: Optional[str] = ""

    keys: Optional[Key] = None
    borrowers: Optional[Borrower] = None

    def __post_init__(self):
        self.id = str(uuid4())
        self.borrowed_at = datetime.datetime.now().isoformat()
        self.borrowed = True

    @classmethod
    def from_objects(cls, key: Key, borrowed_by: Borrower, files: Files):
        return cls(
            key=key.id,
            borrowed_by=borrowed_by.id,
            image_filename=files.image_filename,
            signature_filename=files.signature_filename
        )


@dataclasses.dataclass
class BorrowedKeyResponse:
    id: str
    key: Key
    borrowed_by: Borrower
    image_filename: str
    signature_filename: str
    borrowed: bool
    borrowed_at: str
    returned_at: str

    @classmethod
    def from_supabase(cls, borrowed_key: dict) -> Self:
        return cls(
            id=borrowed_key["id"],
            key=Key(borrowed_key["keys"]["number"], borrowed_key["keys"]["building"], borrowed_key["keys"]["room"], borrowed_key["key"]),
            borrowed_by=Borrower(borrowed_key["borrowers"]["name"], borrowed_key["borrowers"]["company"], borrowed_key["borrowers"]["type"], borrowed_key["borrowed_by"]),
            image_filename=borrowed_key["image_filename"],
            signature_filename=borrowed_key["signature_filename"],
            borrowed=borrowed_key["borrowed"],
            borrowed_at=borrowed_key["borrowed_at"],
            returned_at=borrowed_key["returned_at"]
        )


def get_borrowed_keys(limit: int = 20, offset: int = 0, borrowed: bool = None) -> list[BorrowedKeyResponse]:
    if borrowed is None:
        borrowed_keys = supabase.table("borrowed_keys").select("*", "keys(number, building, room)", "borrowers(name, company, type)").limit(limit).offset(offset).execute()
    else:
        borrowed_keys = supabase.table("borrowed_keys").select("*", "keys(number, building, room)", "borrowers(name, company, type)").eq("borrowed", borrowed).limit(limit).offset(offset).execute()

    return [BorrowedKeyResponse.from_supabase(borrowed_key) for borrowed_key in borrowed_keys.data]


def get_borrowed_key(borrow_id: str):
    borrowed_key = supabase.table("borrowed_keys").select("*", "keys(number, building, room)", "borrowers(name, company, type)").eq("id", borrow_id).eq("borrowed", True).execute()
    if len(borrowed_key.data) == 0:
        return None
    return BorrowedKeyResponse.from_supabase(borrowed_key.data[0])


def does_key_exist(key_id: str):
    key = supabase.table("keys").select("*").eq("id", key_id).execute()
    if len(key.data) == 0:
        return False
    return True

def does_borrower_exist(borrower_id: str):
    borrower = supabase.table("borrowers").select("*").eq("id", borrower_id).execute()
    if len(borrower.data) == 0:
        return False
    return True

def add_key(key: Key):
    supabase.table("keys").insert([
        {
            "id": key.id,
            "number": key.number,
            "building": key.building,
            "room": key.room
        }
    ]).execute()

    return key

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

def add_borrowed_key(key: Key, borrowed_by: Borrower, files: Files):
    # get the current time and date in iso format
    if is_key_borrowed(key.id):
        raise ValueError("Key already borrowed")

    if not does_key_exist(key.id):
        add_key(key)

    if not does_borrower_exist(borrowed_by.id):
        add_borrower(borrowed_by)

    borrowed_key = BorrowedKey.from_objects(key, borrowed_by, files)

    supabase.table("borrowed_keys").insert([
        {
            "id": borrowed_key.id,
            "key": borrowed_key.key,
            "borrowed_by": borrowed_key.borrowed_by,
            "image_filename": borrowed_key.image_filename,
            "signature_filename": borrowed_key.signature_filename,
            "borrowed": borrowed_key.borrowed,
            "borrowed_at": borrowed_key.borrowed_at,
        }
    ]).execute()

    return borrowed_key

def return_borrowed_key(borrow_id: str):
    borrowed_key = get_borrowed_key(borrow_id)
    if borrowed_key is None:
        raise ValueError("Borrowed key not found")

    borrowed_key.returned_at = datetime.datetime.now().isoformat()
    borrowed_key.borrowed = False

    supabase.table("borrowed_keys").update({
        "borrowed": borrowed_key.borrowed,
        "returned_at": borrowed_key.returned_at
    }).eq("id", borrow_id).execute()

    return borrowed_key

def is_key_borrowed(key_id: str):
    borrowed_key_with_key_id = supabase.table("borrowed_keys").select("*").eq("key", key_id).eq("borrowed", True).execute()
    if len(borrowed_key_with_key_id.data) > 0:
        return True
    return False
