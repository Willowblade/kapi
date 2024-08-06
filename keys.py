import dataclasses
import datetime
from typing import Optional
from uuid import uuid4

# from supabase import create_client, Client
#
# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_KEY")
#
# supabase: Client = create_client(url, key)

@dataclasses.dataclass
class Key:
    id: str
    building: str
    room: str


@dataclasses.dataclass
class Borrower:
    name: str
    company: str
    type: str

@dataclasses.dataclass
class Files:
    image_filename: str
    signature_filename: str

@dataclasses.dataclass
class BorrowedKey:
    key: Key
    borrowedBy: Borrower
    files: Files
    borrowed: Optional[bool] = True
    borrowedAt: Optional[str] = ""
    returnedAt: Optional[str] = ""
    id: Optional[str] = ""

    def __post_init__(self):
        self.id = str(uuid4())
        self.borrowedAt = datetime.datetime.now().isoformat()
        self.borrowed = True



borrowed_keys: list[BorrowedKey] = []


def get_currently_borrowed_keys():
    return list(filter(lambda x: x.borrowed, borrowed_keys))

def get_borrowed_key(borrow_id: str):
    for borrowed_key in borrowed_keys:
        if borrowed_key.id == borrow_id:
            return borrowed_key

    return None

def get_all_borrow_events(limit: int, offset: int):
    if limit < 0 or offset < 0:
        raise ValueError("Limit and offset must be greater than 0")

    if offset > len(borrowed_keys):
        return []

    if (offset + limit) > len(borrowed_keys):
        return borrowed_keys[offset:]

    return borrowed_keys[offset:offset + limit]


def add_borrowed_key(key: Key, borrowedBy: Borrower, files: Files):
    # get the current time and date in iso format
    if is_key_borrowed(key.id):
        raise ValueError("Key already borrowed")

    borrowed_key = BorrowedKey(key, borrowedBy, files)

    borrowed_keys.append(borrowed_key)

    return borrowed_key

def return_key(borrow_id: str):
    for borrowed_key in borrowed_keys:
        if borrowed_key.id == borrow_id:
            borrowed_key.borrowed = False
            borrowed_key.returnedAt = datetime.datetime.now().isoformat()
            return borrowed_key

def is_key_borrowed(key_id: str):
    for borrowed_key in borrowed_keys:
        if borrowed_key.key.id == key_id and borrowed_key.borrowed:
            return True

    return False