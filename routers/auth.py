from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

import database.models as models
from database.database import engine, SessionLocal

SECRET_KEY = "j$Di!zrj*FBhl2Nv"
ALGORITHM = "HS256"

router = APIRouter(
    prefix='/auth',
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)

models.Base.metadata.create_all(bind=engine)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oath2_bearer = OAuth2PasswordBearer(tokenUrl="token")


class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def hash_password(password: str):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db) -> any:
    user = db.query(models.Users).filter(models.Users.username == username).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(token: str = Depends(oath2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise get_user_exception()


def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    encode = {
        "sub": username,
        "id": user_id,
        "exp": expire
    }

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/create/user")
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    create_user_model = models.Users()
    create_user_model.username = user.username
    create_user_model.email = user.email
    create_user_model.first_name = user.first_name
    create_user_model.last_name = user.last_name
    create_user_model.hashed_password = hash_password(user.password)
    create_user_model.is_active = True

    db.add(create_user_model)
    db.commit()

    return http_respond(status.HTTP_201_CREATED)


@router.post("/token")
async def login_get_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise token_exception()
    token = create_access_token(user.username, user.id, expires_delta=timedelta(minutes=20))

    return {"token": token}


def http_respond(http_status: status, transaction: str = "successful"):
    return {
        "status": http_status,
        "transaction": transaction,
    }


# Exceptions
def get_user_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credential",
        headers={"WWW-Authenticate": "Bearer"}
    )


def token_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )


if __name__ == "__main__":
    uvicorn.run("auth:app", port=9000, reload=True)
