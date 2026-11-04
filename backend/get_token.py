import getpass
import os

import httpx
#httpx is a library for sending HTTP requests from Python. It's the opposite role from FastAPI, which receives them.

from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")

email = input("Email: ")
password = getpass.getpass("Password: ")   # typing is hidden, like sudo

response = httpx.post(
    f"{SUPABASE_URL}/auth/v1/token",
    params={"grant_type": "password"},
    headers={"apikey": os.environ["SUPABASE_ANON_KEY"]},
    json={"email": email, "password": password},
)
response.raise_for_status()                # crash with a clear message if login failed
print(response.json()["access_token"])
