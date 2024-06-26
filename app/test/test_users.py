from fastapi.testclient import TestClient
from src.main import app
from src.database.operations.user import create_user, find_user, delete_user
from src.database import get_database, clean_database
from src.models.user import UserIn
from bson import ObjectId
from test.data.user_json import new_user_json


def test_create_user():
    with TestClient(app):
        clean_database()
        database = get_database()
        new_user = create_user(database, UserIn(**new_user_json[0]))
        new_user_id = new_user.id

        user = find_user(database, ObjectId(new_user_id))

        assert user.id == new_user_id


def test_delete_user():
    with TestClient(app):
        clean_database()
        database = get_database()
        new_user = create_user(
            database, UserIn(**new_user_json[0])
        ).model_dump()
        new_user_id = new_user["id"]

        delete_user(database, ObjectId(new_user_id))

        user = find_user(database, ObjectId(new_user_id))

        assert user is None
