import unittest

from keys import get_borrowed_key, Key, Borrower, get_currently_borrowed_keys, get_all_borrow_events, borrowed_keys, \
    is_key_borrowed, add_borrowed_key, return_key, Files


class TestKeys(unittest.TestCase):

    def setUp(self):
        borrowed_keys.clear()

    def test_borrow_key(self):
        key_id = "1"
        key_building = "Building 1"
        key_room = "Room 1"
        borrower_name = "John Doe"
        borrower_company = "Company 1"
        borrower_type = "Employee"
        image_filename = "image.jpg"
        signature_filename = "signature.jpg"

        add_borrowed_key(
            Key(id=key_id, building=key_building, room=key_room),
            Borrower(name=borrower_name, company=borrower_company, type=borrower_type),
            Files(image_filename=image_filename, signature_filename=signature_filename)
        )

        self.assertTrue(is_key_borrowed(key_id))

    def test_return_key(self):
        key_id = "1"
        key_building = "Building 1"
        key_room = "Room 1"
        borrower_name = "John Doe"
        borrower_company = "Company 1"
        borrower_type = "Employee"
        image_filename = "image.jpg"
        signature_filename = "signature.jpg"

        borrow = add_borrowed_key(
            Key(id=key_id, building=key_building, room=key_room),
            Borrower(name=borrower_name, company=borrower_company, type=borrower_type),
            Files(image_filename=image_filename, signature_filename=signature_filename)
        )

        return_key(borrow.id)
        borrowed_key = get_borrowed_key(borrow.id)
        self.assertIsNotNone(borrowed_key)
        self.assertFalse(borrowed_key.borrowed)

        borrowed_keys = get_currently_borrowed_keys()
        self.assertEqual(len(borrowed_keys), 0)

        all_borrowed_events = get_all_borrow_events(20, 0)
        self.assertEqual(len(all_borrowed_events), 1)

    def test_duplicate_borrow(self):
        key_id = "1"
        key_building = "Building 1"
        key_room = "Room 1"
        borrower_name = "John Doe"
        borrower_company = "Company 1"
        borrower_type = "Employee"
        image_filename = "image.jpg"
        signature_filename = "signature.jpg"

        add_borrowed_key(
            Key(id=key_id, building=key_building, room=key_room),
            Borrower(name=borrower_name, company=borrower_company, type=borrower_type),
            Files(image_filename=image_filename, signature_filename=signature_filename)
        )

        with self.assertRaises(ValueError):
            add_borrowed_key(
                Key(id=key_id, building=key_building, room=key_room),
                Borrower(name=borrower_name, company=borrower_company, type=borrower_type),
                Files(image_filename=image_filename, signature_filename=signature_filename)
            )
