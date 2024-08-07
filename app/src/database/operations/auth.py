import logging
import time

from passlib.context import CryptContext
from src.database.operations.user import find_unsecure_user_by_email
from src.database import get_database
from datetime import datetime, timedelta
from jose import JWTError, jwt

from src.exceptions import UnauthorizedException
from src.utils import config, DotEnvConfig
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from src.models.auth import TokenDataE, Token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = config.get_config(DotEnvConfig.ENV_AUTH_SECRET_KEY)
ALGORITHM = config.get_config(DotEnvConfig.ENV_AUTH_ALGORITHM)
ACCESS_TOKEN_EXPIRE_MINUTES = config.get_config(
    DotEnvConfig.ENV_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, expires_delta: timedelta or None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_login_access_token(
    database, email, expires_delta: timedelta or None = None
):
    # TODO: token can be stored in database so it can be invalidated
    data = {"sub": email}

    return create_access_token(data, expires_delta)


def get_auth_user(database, email: str, password: str):
    auth_user_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = find_unsecure_user_by_email(database, email)

    if not user:
        logging.info(
            "Failed login for user %s - incorrect username/email", email
        )
        raise auth_user_credentials_exception

    user = user.model_dump()

    if not verify_password(password, user["hashed_password"]):
        logging.info("Failed login for user %s - incorrect password", email)
        raise auth_user_credentials_exception

    return user


credentials_exception = UnauthorizedException("Invalid token.")


def get_current_user(database, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        expires = payload.get("exp", 0)
        if expires < time.time():
            raise credentials_exception
        if email is None:
            raise credentials_exception
        token_tada = TokenDataE(email=email)
    except JWTError:
        raise credentials_exception
    user = find_unsecure_user_by_email(database, token_tada.email)
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    database=Depends(get_database), token: str = Depends(oauth2_scheme)
):
    try:
        current_user = get_current_user(database, token)
    except UnauthorizedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            # print("No username")
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return "verified"  # return admin when multi-admin implemented


def create_user_access_token(
    database, email: str, password: str, expires_in_minutes: int = 15
) -> Token:
    logging.info("Creating token for user %s", email)
    user = get_auth_user(database, email=email, password=password)

    access_token_expires = timedelta(minutes=int(expires_in_minutes))

    access_token = create_login_access_token(
        database, email=user["email"], expires_delta=access_token_expires
    )

    return Token(**{"access_token": access_token, "token_type": "Bearer"})


def create_admin_access_token(
    email: str, password: str, expires_in_minutes: int = 15
) -> Token:
    if not (
        email == config.get_config(config.ENV_ADMIN_EMAIL)
        and password == config.get_config(config.ENV_ADMIN_PASSWORD)
    ):
        raise UnauthorizedException()

    access_token_expires = timedelta(minutes=int(expires_in_minutes))

    data = {"sub": email}

    access_token = create_access_token(
        data, expires_delta=access_token_expires
    )

    return Token(**{"access_token": access_token, "token_type": "Bearer"})
