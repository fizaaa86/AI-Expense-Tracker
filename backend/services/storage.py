"""Saving receipt photos in Supabase Storage.
Every call uses the USER's token, so the storage policies only allow their own folder."""
import os
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
BUCKET = "receipts"

EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic"}


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "apikey": ANON_KEY}


def upload_receipt_image(token: str, user_id: uuid.UUID, image: bytes, mime_type: str) -> str:
    """Save the photo as receipts/<user_id>/<random id>.jpg and return that path."""
    path = f"{user_id}/{uuid.uuid4()}.{EXTENSIONS.get(mime_type, 'img')}"
    response = httpx.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}",
        headers={**_headers(token), "Content-Type": mime_type},
        content=image,
        timeout=30,
    )
    response.raise_for_status()      # turns a 4xx/5xx answer into an error we can catch
    return path


def signed_url(token: str, path: str, expires_in: int = 3600) -> str:
    """A temporary link to a private photo (default: valid for 1 hour)."""
    response = httpx.post(
        f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET}/{path}",
        headers=_headers(token),
        json={"expiresIn": expires_in},
        timeout=30,
    )
    response.raise_for_status()
    return f"{SUPABASE_URL}/storage/v1{response.json()['signedURL']}"


def download_receipt_image(token: str, path: str) -> tuple[bytes, str]:
    """Fetch a stored photo. Returns (image bytes, mime type such as 'image/jpeg')."""
    response = httpx.get(
        f"{SUPABASE_URL}/storage/v1/object/authenticated/{BUCKET}/{path}",
        headers=_headers(token),
        timeout=30,
    )
    response.raise_for_status()
    return response.content, response.headers.get("content-type", "image/jpeg")
