import os
import json

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import event, text
from sqlalchemy.orm import sessionmaker   
from fastapi import Depends
from auth import CurrentUser, get_current_user



load_dotenv()  # reads backend/.env into environment variables

# Supabase gives "postgresql://...", SQLAlchemy needs to be told which driver: "postgresql+psycopg://..."
DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)  # pre_ping: test a connection before using it

#sessionmaker makes a session factory-SessionLocal which is binded to the engine
#The engine knows how to connect python to postgresql
SessionLocal = sessionmaker(bind=engine)

#yield hands the session to the endpoint. When the endpoint finishes, the code continues after yield, the with block ends, and the session is closed. This means there's no leaked connection, even if there's an error.

def get_db():
    """FastAPI dependency: one session per request, always closed afterwards."""
    with SessionLocal() as db:
        yield db


#set_config('request.jwt.claims', ...) hands the verified token's contents to Postgres. That's what auth.uid() reads, so your RLS policies and default auth.uid() now work
#set local role authenticated switches from the admin account to the limited authenticated role, which must obey RLS.
#local / true mean "only until this transaction ends". That's essential: connections are reused from the pool, and without local the next request, perhaps from a different user, would inherit this user's identity.
#Why after_begin rather than just running it once? After db.commit() a new transaction starts, for example during db.refresh(), and the local settings are already gone. Hooking into "every transaction start" makes sure we're never accidentally back to admin.


def get_user_db(user: CurrentUser = Depends(get_current_user)):
    """A session where every transaction runs AS the logged-in user, so RLS applies."""
    claims = json.dumps(user.claims)

    with SessionLocal() as db:
        # Runs at the START of every transaction in this session
        @event.listens_for(db, "after_begin")
        def act_as_user(session, transaction, connection):
            connection.execute(
                text("select set_config('request.jwt.claims', :claims, true)"),
                {"claims": claims},
            )
            connection.execute(text("set local role authenticated"))

        yield db
