import dataclasses
import datetime
from typing import Optional, Self, Tuple
from uuid import uuid4

from postgrest.types import CountMethod

from kapi.db.borrowers import Borrower, does_borrower_exist, add_borrower
from kapi.db.db import supabase
from kapi.db.reservations import does_reservation_exist, get_reservation_for_borrow_key
from kapi.db.keys import Key, does_key_exist, add_key


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
    borrower: Borrower
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
            key=Key(
                borrowed_key["keys"]["room_number"],
                borrowed_key["keys"]["building_id"],
                borrowed_key["keys"]["type"],
                borrowed_key["key_id"]
            ),
            borrower=Borrower(
                name=borrowed_key["borrowers"]["name"],
                type=borrowed_key["borrowers"]["type"],
                company=borrowed_key["borrowers"].get("company"),
                id=borrowed_key["borrower_id"],
                email=borrowed_key["borrowers"].get("email"),
                phone=borrowed_key["borrowers"].get("phone")
            ),
            image_filename=borrowed_key["image_filename"],
            signature_filename=borrowed_key["signature_filename"],
            building_id=borrowed_key["building_id"],
            borrowed=borrowed_key["borrowed"],
            borrowed_at=borrowed_key["borrowed_at"],
            returned_at=borrowed_key["returned_at"]
        )


def get_borrowed_keys(limit: int = 20, offset: int = 0, borrowed: bool = None, building_id: str = None) -> Tuple[list[BorrowedKeyResponse], int]:
    query = supabase.table("borrowed_keys").select("*", "keys(*)", "borrowers(*)", count=CountMethod.exact)
    if borrowed is not None:
        query = query.eq("borrowed", borrowed)
    if building_id is not None:
        query = query.eq("building_id", building_id)
    # sort by borrowed_at desc default
    query = query.order("borrowed_at", desc=True)
    borrowed_keys = query.limit(limit).offset(offset).execute()

    return [BorrowedKeyResponse.from_supabase(borrowed_key) for borrowed_key in borrowed_keys.data], borrowed_keys.count


def get_borrowed_key(borrow_id: str):
    borrowed_key = supabase.table("borrowed_keys").select("*", "keys(*)", "borrowers(*)").eq("id", borrow_id).execute()
    if len(borrowed_key.data) == 0:
        return None
    return BorrowedKeyResponse.from_supabase(borrowed_key.data[0])


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


def is_key_borrowed(key_id: str):
    borrowed_key_with_key_id = supabase.table("borrowed_keys").select("*").eq("key_id", key_id).eq("borrowed", True).execute()
    if len(borrowed_key_with_key_id.data) > 0:
        return True
    return False


def return_borrowed_key(borrow_id: str):
    borrowed_key = get_borrowed_key(borrow_id)
    if borrowed_key is None:
        raise ValueError("Borrowed key not found")
    if not borrowed_key.borrowed:
        raise ValueError("Key already returned")

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
