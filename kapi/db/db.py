import os

from supabase import create_client, Client

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_ANON_KEY")

print(f"Connecting to Supabase with {url=}, {key=}")

supabase: Client = create_client(url, key)

print(f"Connected to Supabase")

# TODO we could make it more class based instead of current function based, as we already have the classes defined



