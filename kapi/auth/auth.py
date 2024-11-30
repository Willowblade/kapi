from kapi.db.db import supabase, url, key

from supabase import create_client, Client


def user_login(email: str, password: str):
    new_client = create_client(url, key)
    user = new_client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return user