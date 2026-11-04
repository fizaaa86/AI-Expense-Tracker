#extract the tokens from the header and verify the signature against the public key,
#if verified creates an object of CurrentUser with uid and claims and return it,any request can make use of this to check if correct user it is before proceeding


import os
import uuid
from dataclasses import dataclass

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
ISSUER = f"{SUPABASE_URL}/auth/v1"

# Downloads Supabase's PUBLIC keys once and caches them
jwks_client = jwt.PyJWKClient(f"{ISSUER}/.well-known/jwks.json")

bearer = HTTPBearer()   # reads the "Authorization: Bearer <token>" header (adds the Authorize button in /docs)


@dataclass
class CurrentUser:
    id: uuid.UUID
    claims: dict        # the whole verified payload; the database needs it for RLS
    token: str          # the raw token; Supabase Storage needs it so storage policies apply

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> CurrentUser:
    token = creds.credentials
    try:
        key = jwks_client.get_signing_key_from_jwt(token).key   # pick the right public key
        claims = jwt.decode(
            token,
            key,
            algorithms=["ES256"],          # only accept this algorithm (prevents algorithm-swap attacks)
            audience="authenticated",      # token must be meant for logged-in users
            issuer=ISSUER,                 # token must come from YOUR Supabase project
        )                                  # also checks "exp": expired tokens are rejected
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(id=uuid.UUID(claims["sub"]), claims=claims, token=token)

