"""Projects HTTP API against PostgreSQL."""

from datetime import datetime
from http import HTTPStatus
from typing import Any, cast
from uuid import uuid4

from httpx import AsyncClient

PROJECTS_URL = "/api/v1/projects"


async def create_project(
    client: AsyncClient, name: str = "Website", description: str = ""
) -> dict[str, Any]:
    response = await client.post(
        PROJECTS_URL, json={"name": name, "description": description}
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return cast(dict[str, Any], response.json())


async def test_create_then_get_a_project(client: AsyncClient) -> None:
    created = await create_project(client, name="  Website ", description="Site")

    response = await client.get(f"{PROJECTS_URL}/{created['id']}")

    assert created["name"] == "Website"
    assert created["status"] == "active"
    assert response.status_code == HTTPStatus.OK
    assert response.json() == created


async def test_duplicate_name_is_a_conflict(client: AsyncClient) -> None:
    await create_project(client, name="Website")

    response = await client.post(PROJECTS_URL, json={"name": "Website"})

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "project_name_already_exists"


async def test_blank_name_is_rejected_by_the_domain(client: AsyncClient) -> None:
    response = await client.post(PROJECTS_URL, json={"name": "   "})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "invalid_project_name"


async def test_malformed_body_is_a_request_validation_error(
    client: AsyncClient,
) -> None:
    response = await client.post(PROJECTS_URL, json={"description": "no name"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "request_validation_error"


async def test_unknown_project_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{PROJECTS_URL}/{uuid4()}")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "project_not_found"


async def test_update_a_project(client: AsyncClient) -> None:
    project = await create_project(client)

    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}",
        json={"name": "Intranet", "description": "Internal"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert (body["name"], body["description"]) == ("Intranet", "Internal")
    assert datetime.fromisoformat(body["updated_at"]) > datetime.fromisoformat(
        project["updated_at"]
    )


async def test_renaming_to_an_existing_name_is_a_conflict(client: AsyncClient) -> None:
    await create_project(client, name="Website")
    project = await create_project(client, name="Intranet")

    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}", json={"name": "Website"}
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "project_name_already_exists"


async def test_archive_a_project(client: AsyncClient) -> None:
    project = await create_project(client)
    url = f"{PROJECTS_URL}/{project['id']}"

    archived = await client.post(f"{url}/archive")
    archived_again = await client.post(f"{url}/archive")
    updated = await client.patch(url, json={"name": "Other"})

    assert archived.status_code == HTTPStatus.OK
    assert archived.json()["status"] == "archived"
    assert archived_again.status_code == HTTPStatus.CONFLICT
    assert archived_again.json()["code"] == "project_already_archived"
    assert updated.status_code == HTTPStatus.CONFLICT
    assert updated.json()["code"] == "project_archived"


async def test_delete_a_project(client: AsyncClient) -> None:
    project = await create_project(client)
    url = f"{PROJECTS_URL}/{project['id']}"

    deleted = await client.delete(url)
    fetched = await client.get(url)
    deleted_again = await client.delete(url)

    assert deleted.status_code == HTTPStatus.NO_CONTENT
    assert deleted.content == b""
    assert fetched.status_code == HTTPStatus.NOT_FOUND
    assert deleted_again.status_code == HTTPStatus.NOT_FOUND


async def test_list_projects_filters_sorts_and_paginates(client: AsyncClient) -> None:
    projects = {
        name: await create_project(client, name=name)
        for name in ("Gamma", "Alpha", "Beta")
    }
    await client.post(f"{PROJECTS_URL}/{projects['Beta']['id']}/archive")

    response = await client.get(
        PROJECTS_URL, params={"status": "active", "sort": "name", "size": 1, "page": 2}
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert [item["name"] for item in body["items"]] == ["Gamma"]
    assert (body["total"], body["page"], body["size"], body["pages"]) == (2, 2, 1, 2)


async def test_list_projects_search_matches_wildcards_literally(
    client: AsyncClient,
) -> None:
    await create_project(client, name="50% off")
    await create_project(client, name="500 offers")

    response = await client.get(PROJECTS_URL, params={"search": "50%"})

    assert [item["name"] for item in response.json()["items"]] == ["50% off"]


async def test_list_projects_rejects_an_unknown_sort_field(client: AsyncClient) -> None:
    response = await client.get(PROJECTS_URL, params={"sort": "-description"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "invalid_sort_field"
