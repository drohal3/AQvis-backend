from fastapi.testclient import TestClient
from src.main import app
from src.database import clean_database

from test.data.organisation_json import new_organisation_json
from test.data.user_json import new_user_json
from test.functions import get_admin_header

new_organisation_data = new_organisation_json[0]
new_user_data = new_user_json[0]


def test_create_organisation_api():
    with TestClient(app) as client:
        clean_database()
        response = client.post(
            "/admin/organisations",
            json=new_organisation_data,
            headers=get_admin_header(),
        )
        assert response.status_code == 201


def test_create_organisation_api_unauthorized():
    with TestClient(app) as client:
        clean_database()
        response = client.post(
            "/admin/organisations", json=new_organisation_data
        )
        assert response.status_code == 401


def test_get_organisation_api():
    with TestClient(app) as client:
        clean_database()
        new_organisation = client.post(
            "/admin/organisations",
            json=new_organisation_data,
            headers=get_admin_header(),
        )

        new_organisation_id = new_organisation.json()["id"]

        response = client.get(
            f"/admin/organisations/{new_organisation_id}",
            headers=get_admin_header(),
        )
        assert response.status_code == 200
        assert response.json()["id"] == new_organisation_id


def test_get_organisation_api_unauthorized():
    with TestClient(app) as client:
        clean_database()
        new_organisation_id = "000000000000000000000000"

        response = client.get(
            f"/admin/organisations/{new_organisation_id}",
        )
        assert response.status_code == 401


def test_get_organisation_api_not_exist():
    with TestClient(app) as client:
        clean_database()
        new_organisation_id = "000000000000000000000000"
        response = client.get(
            f"/admin/organisations/{new_organisation_id}",
            headers=get_admin_header(),
        )
        assert response.status_code == 404


def test_delete_organisation_api():
    with TestClient(app) as client:
        clean_database()
        response = client.post(
            "/admin/organisations",
            json=new_organisation_data,
            headers=get_admin_header(),
        )
        organisation_id = response.json()["id"]

        response = client.delete(
            f"/admin/organisations/{organisation_id}",
            headers=get_admin_header(),
        )
        assert response.status_code == 204

        response = client.get(
            f"/admin/organisations/{organisation_id}",
            headers=get_admin_header(),
        )

        assert response.status_code == 404


def test_delete_organisation_api_unauthorized():
    with TestClient(app) as client:
        clean_database()

        organisation_id = "000000000000000000000000"

        response = client.delete(
            f"/admin/organisations/{organisation_id}",
        )
        assert response.status_code == 401


def test_delete_organisation_api_not_exist():
    with TestClient(app) as client:
        clean_database()
        some_id = "000000000000000000000000"
        response = client.delete(
            f"/admin/organisations/{some_id}", headers=get_admin_header()
        )
        assert response.status_code == 404


def test_add_and_remove_member_api():
    with TestClient(app) as client:
        clean_database()
        organisation_response = client.post(
            "/admin/organisations",
            json=new_organisation_data,
            headers=get_admin_header(),
        )
        organisation_id = organisation_response.json()["id"]
        user_response = client.post(
            "admin/users", json=new_user_data, headers=get_admin_header()
        )
        user_id = user_response.json()["id"]

        member_json = {"organisation": organisation_id, "user": user_id}
        response = client.post(
            "/admin/organisations/add_user",
            json=member_json,
            headers=get_admin_header(),
        )
        assert response.status_code == 200

        response = client.post(
            "/admin/organisations/remove_user",
            json=member_json,
            headers=get_admin_header(),
        )
        assert response.status_code == 200


def test_add_and_remove_member_api_unauthorized():
    with TestClient(app) as client:
        clean_database()

        member_json = {
            "organisation": "000000000000000000000000",
            "user": "000000000000000000000000",
        }
        response = client.post(
            "/admin/organisations/add_user",
            json=member_json,
        )
        assert response.status_code == 401

        response = client.post(
            "/admin/organisations/remove_user",
            json=member_json,
        )
        assert response.status_code == 401


def test_add_member_api_already_exist():
    with TestClient(app) as client:
        clean_database()

        organisation_response = client.post(
            "/admin/organisations",
            json=new_organisation_data,
            headers=get_admin_header(),
        )
        organisation_id = organisation_response.json()["id"]

        user_response = client.post(
            "admin/users", json=new_user_data, headers=get_admin_header()
        )
        user_id = user_response.json()["id"]

        member_json = {"organisation": organisation_id, "user": user_id}

        client.post(
            "/admin/organisations/add_user",
            json=member_json,
            headers=get_admin_header(),
        )
        response = client.post(
            "/admin/organisations/add_user",
            json=member_json,
            headers=get_admin_header(),
        )

        assert response.status_code == 409
