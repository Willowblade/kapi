from kapi.db.db import supabase


def user_login(email: str, password: str):
    user = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return user