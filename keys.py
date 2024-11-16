import dataclasses
import datetime
import os
import uuid
from gc import collect
from optparse import Option
from typing import Optional, Any, Self, Tuple
from uuid import uuid4, uuid5

from postgrest.types import CountMethod
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

print(f"Connecting to Supabase with {url=}, {key=}")

supabase: Client = create_client(url, key)

print(f"Connected to Supabase")



BORROWER_UUID5_NAMESPACE = uuid.UUID("50ad06e6-5abe-48d2-8912-148077032ae0")
BUILDING_UUID5_NAMESPACE = uuid.UUID("50ad06e6-5abe-48d2-8912-148077032aee")

# keys = supabase.table("keys").select("*").execute()
# borrowers = supabase.table("borrowers").select("*").execute()
# borrowed_keys = supabase.table("borrowed_keys").select("*").execute()
# print("Keys", keys)
# print("Borrowers", borrowers)
# print("Borrowed Keys", borrowed_keys)



# TODO we could make it more class based instead of current function based, as we already have the classes defined

@dataclasses.dataclass
class Building:
    name: str
    id: Optional[str] = ""

    def __post_init__(self):
        if self.id == "":
            self.id = str(uuid5(BUILDING_UUID5_NAMESPACE, self.name))


def get_all_buildings(limit: int = 20, offset: int=0, search: str = None) -> Tuple[list[Building], int]:
    query = supabase.table("buildings").select("*", count=CountMethod.exact)
    if search is not None:
        query = query.ilike("name", f"%{search}%")
    buildings = query.limit(limit).offset(offset).execute()
    return [Building(building["name"], id=building["id"]) for building in buildings.data], buildings.count

def add_building(name: str):
    building = Building(name)
    supabase.table("buildings").insert([
        {
            "id": building.id,
            "name": building.name
        }
    ]).execute()
    return building

@dataclasses.dataclass
class Key:
    room_number: str
    building_id: str
    type: str
    id: Optional[str] = ""

    def __post_init__(self):
        self.id = f"{self.building_id}-{self.room_number}-{self.type}"

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
    key_id: str # ID of the key
    borrower_id: str # ID of the borrower
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
    def from_objects(cls, key: Key, borrower_id: Borrower, files: Files):
        return cls(
            key_id=key.id,
            borrower_id=borrower_id.id,
            image_filename=files.image_filename,
            signature_filename=files.signature_filename
        )


@dataclasses.dataclass
class BorrowedKeyResponse:
    id: str
    key: Key
    borrower_id: Borrower
    image_filename: str
    building_id: str
    signature_filename: str
    borrowed: bool
    borrowed_at: str
    returned_at: str

    @classmethod
    def from_supabase(cls, borrowed_key: dict) -> Self:
        return cls(
            id=borrowed_key["id"],
            key=Key(borrowed_key["keys"]["room_number"], borrowed_key["keys"]["building_id"], borrowed_key["keys"]["type"], borrowed_key["key_id"]),
            borrower_id=Borrower(borrowed_key["borrowers"]["name"], borrowed_key["borrowers"]["type"], borrowed_key["borrowers"]["company"], borrowed_key["borrower_id"]),
            image_filename=borrowed_key["image_filename"],
            signature_filename=borrowed_key["signature_filename"],
            building_id=borrowed_key["building_id"],
            borrowed=borrowed_key["borrowed"],
            borrowed_at=borrowed_key["borrowed_at"],
            returned_at=borrowed_key["returned_at"]
        )


@dataclasses.dataclass
class KeyReservation:
    key_id: str
    id: Optional[str] = None
    collected: bool = False
    returned: bool = False
    created_at: Optional[str] = None
    borrower_id: Optional[str] = None
    collection_at: Optional[str] = None
    reservation_by: Optional[str] = None
    return_at: Optional[str] = None
    borrowed_key_id: Optional[str] = None

    def __post_init__(self):
        self.id = str(uuid4())
        self.created_at = datetime.datetime.now().isoformat()


@dataclasses.dataclass
class KeyReservationResponse:
    id: str
    key: Key
    created_at: str
    # both extra metadata for easier querying
    collected: bool = False
    returned: bool = False
    borrower: Optional[Borrower] = None
    collection_at: Optional[str] = None
    reservation_by: Optional[str] = None
    return_at: Optional[str] = None
    borrowed_key_id: Optional[str] = None

    @classmethod
    def from_supabase(cls, key_reservation: dict) -> Self:
        borrower = None

        if key_reservation.get("borrowers") is not None:
            borrower = Borrower(key_reservation["borrowers"]["name"], key_reservation["borrowers"]["type"], key_reservation["borrowers"]["company"], key_reservation["borrower_id"])

        return cls(
            id=key_reservation["id"],
            key=Key(key_reservation["keys"]["room_number"], key_reservation["keys"]["building_id"], key_reservation["keys"]["type"], key_reservation["key_id"]),
            created_at=key_reservation["created_at"],
            borrower=borrower,
            collection_at=key_reservation.get("collection_at"),
            reservation_by=key_reservation.get("reservation_by"),
            return_at=key_reservation.get("return_at"),
            borrowed_key_id=key_reservation.get("borrowed_key_id"),
            collected=key_reservation.get("collected"),
            returned=key_reservation.get("returned")
        )

def add_reservation(key: Key, borrower: Borrower, description: str, collection_at: str, reservation_by: str, return_at: str = None):
    if not does_key_exist(key.id):
        add_key(key)

    if borrower and not does_borrower_exist(borrower.id):
        add_borrower(borrower)

    reservation = supabase.table("key_reservations").insert([
        {
            "key_id": key.id,
            "description": description,
            "borrower_id": borrower.id if borrower is not None else None,
            "building_id": key.building_id,
            "collection_at": collection_at,
            "reservation_by": reservation_by,
            "return_at": return_at
        }
    ]).execute().data[0]

    print("Created reservation", reservation)
    return reservation

def get_reservations(limit: int = 20, offset: int = 0, collected: bool = None, returned: bool = None, building_id = None) -> Tuple[list[KeyReservationResponse], int]:
    query = supabase.table("key_reservations").select("*", "keys(room_number, building_id, type)", "borrowers(name, company, type)", count=CountMethod.exact)

    if collected is not None:
        query = query.eq("collected", collected)
    if returned is not None:
        query = query.eq("returned", returned)
    if building_id is not None:
        query = query.eq("building_id", building_id)

    reservations = query.limit(limit).offset(offset).execute()

    return [KeyReservationResponse.from_supabase(reservation) for reservation in reservations.data], reservations.count

def get_borrowed_keys(limit: int = 20, offset: int = 0, borrowed: bool = None, building_id = None) -> Tuple[list[BorrowedKeyResponse], int]:
    query = supabase.table("borrowed_keys").select("*", "keys(room_number, building_id, type)", "borrowers(name, company, type)", count=CountMethod.exact)
    if borrowed is not None:
        query = query.eq("borrowed", borrowed)
    if building_id is not None:
        query = query.eq("building_id", building_id)
    borrowed_keys = query.limit(limit).offset(offset).execute()

    return [BorrowedKeyResponse.from_supabase(borrowed_key) for borrowed_key in borrowed_keys.data], borrowed_keys.count


def get_borrowed_key(borrow_id: str):
    borrowed_key = supabase.table("borrowed_keys").select("*", "keys(room_number, building_id, type)", "borrowers(name, company, type)").eq("id", borrow_id).eq("borrowed", True).execute()
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

def does_reservation_exist(reservation_id: str):
    reservation = supabase.table("key_reservations").select("*").eq("id", reservation_id).execute()
    if len(reservation.data) == 0:
        return False
    return True

def get_open_reservation_for_key(key_id: str, borrower_id: str = None):
    # TODO also infer date for the reservation or that's a filter in the frontend?
    reservation = supabase.table("key_reservations").select("*").eq("key_id", key_id).eq("collected", False).execute()
    if len(reservation.data) == 0:
        return None
    return KeyReservationResponse.from_supabase(reservation.data[0])

def get_reservation_for_borrow_key(borrowed_key_id: str):
    reservation = supabase.table("key_reservations").select("*").eq("borrowed_key_id", borrowed_key_id).execute()
    if len(reservation.data) == 0:
        return None
    return reservation.data[0]


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

def add_borrowed_key(key: Key, borrower_id: Borrower, files: Files, reservation_id: str = None):
    # get the current time and date in iso format
    if is_key_borrowed(key.id):
        raise ValueError("Key already borrowed")

    if not does_key_exist(key.id):
        add_key(key)

    if not does_borrower_exist(borrower_id.id):
        add_borrower(borrower_id)

    borrowed_key = BorrowedKey.from_objects(key, borrower_id, files)

    borrowed_key_db = supabase.table("borrowed_keys").insert([
        {
            "id": borrowed_key.id,
            "key_id": borrowed_key.key_id,
            "borrower_id": borrowed_key.borrower_id,
            "image_filename": borrowed_key.image_filename,
            "signature_filename": borrowed_key.signature_filename,
            "borrowed": borrowed_key.borrowed,
            "borrowed_at": borrowed_key.borrowed_at,
            "building_id": key.building_id
        }
    ]).execute()

    if reservation_id:
        if not does_reservation_exist(reservation_id):
            print(f"Reservation {reservation_id} does not exist")
        else:
            borrowed_key_id = borrowed_key_db.data[0]["id"]
            print(f"Linking reservation {reservation_id} to borrowed key {borrowed_key_id}")
            supabase.table("key_reservations").update({
                "collected": True,
                "borrowed_key_id": borrowed_key_id
            }).eq("id", reservation_id).execute()

    # TODO optional future but needs proper testing, auto-infer reservation from data
    # existing_reservation = get_open_reservation_for_key(key.id, borrower=borrowed_key.borrower_id)
    # if existing_reservation:
    #     supabase.table("key_reservations").update({
    #         "collected": True,
    #         "collection_at": datetime.datetime.now().isoformat(),
    #         "borrowed_key_id": borrowed_key_db.data[0]["id"]
    #     }).eq("id", existing_reservation.id).execute()

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

    reservation = get_reservation_for_borrow_key(borrow_id)
    if reservation:
        supabase.table("key_reservations").update({
            "returned": True,
        }).eq("id", reservation["id"]).execute()
        print(f"Updated reservation {reservation['id']} to returned")

    print(f"Returned borrowed key {borrow_id}")
    return borrowed_key

def is_key_borrowed(key_id: str):
    borrowed_key_with_key_id = supabase.table("borrowed_keys").select("*").eq("key_id", key_id).eq("borrowed", True).execute()
    if len(borrowed_key_with_key_id.data) > 0:
        return True
    return False

def delete_reservation(reservation_id: str):
    if not does_reservation_exist(reservation_id):
        raise ValueError("Reservation does not exist")
    deleted_row = supabase.table("key_reservations").delete().eq("id", reservation_id).execute()
    return deleted_row.data[0]