from pymongo.database import Database
from bson import ObjectId

import logging

from src.dependencies.authentication import (
    get_password_hash,
)

from src.models.user import User, NewUser, UnsecureUser


def find_user(database: Database, user_id: ObjectId) -> User | None:
    user = database.users.find_one({"_id": user_id}, {"hashed_password": 0})
    if user is None:
        return user
    user["id"] = str(user["_id"])

    return user


def find_unsecure_user_by_email(
    database: Database, email: str
) -> UnsecureUser | None:
    user = database.users.find_one({"email": email})
    if user is None:
        return user
    user["id"] = str(user["_id"])

    return user


def create_user(database: Database, data: NewUser) -> User:
    password = data.password
    hashed_password = get_password_hash(password)

    new_user_data = data.model_dump()
    new_user_data.pop("password")
    new_user_data["hashed_password"] = hashed_password
    user_id = database.users.insert_one(new_user_data).inserted_id
    logging.debug(f"create_user() - user_id: {user_id}")
    user = find_user(database, user_id)

    logging.info(f"create_user() - created user: {user}")

    return user


def delete_user(database: Database, user_id: ObjectId):
    database.users.delete_one({"_id": user_id})


def add_organisation(
    database: Database, user_id: ObjectId, organisation_id: ObjectId
):
    database.users.update_one(
        {"_id": user_id}, {"$set": {"organisation": str(organisation_id)}}
    )


def remove_organisation(
    database: Database, user_id: ObjectId, organisation_id: ObjectId
):
    database.users.update_one(
        {"_id": user_id}, {"$set": {"organisation": None}}
    )
