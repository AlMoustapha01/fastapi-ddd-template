"""Tasks HTTP API and its interactions with projects, against PostgreSQL."""

from http import HTTPStatus
from typing import Any, cast
from uuid import uuid4

from httpx import AsyncClient, Response

PROJECTS_URL = "/api/v1/projects"
TASKS_URL = "/api/v1/tasks"


async def create_project(client: AsyncClient, name: str = "Website") -> str:
    response = await client.post(PROJECTS_URL, json={"name": name})
    assert response.status_code == HTTPStatus.CREATED, response.text
    return cast(str, response.json()["id"])


async def create_task(
    client: AsyncClient, project_id: str, title: str = "Write copy"
) -> dict[str, Any]:
    response = await client.post(
        TASKS_URL, json={"project_id": project_id, "title": title}
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return cast(dict[str, Any], response.json())


async def change_status(client: AsyncClient, task_id: str, status: str) -> Response:
    return await client.patch(f"{TASKS_URL}/{task_id}/status", json={"status": status})


async def test_create_then_get_a_task(client: AsyncClient) -> None:
    project_id = await create_project(client)
    created = await create_task(client, project_id, title=" Draft ")

    response = await client.get(f"{TASKS_URL}/{created['id']}")

    assert (created["project_id"], created["title"], created["status"]) == (
        project_id,
        "Draft",
        "todo",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == created


async def test_task_for_an_unknown_project_is_not_found(client: AsyncClient) -> None:
    response = await client.post(
        TASKS_URL, json={"project_id": str(uuid4()), "title": "Draft"}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "task_project_not_found"


async def test_task_for_an_archived_project_is_a_conflict(client: AsyncClient) -> None:
    project_id = await create_project(client)
    await client.post(f"{PROJECTS_URL}/{project_id}/archive")

    response = await client.post(
        TASKS_URL, json={"project_id": project_id, "title": "Draft"}
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "task_project_archived"


async def test_update_a_task(client: AsyncClient) -> None:
    task = await create_task(client, await create_project(client))
    url = f"{TASKS_URL}/{task['id']}"

    updated = await client.patch(url, json={"title": "New", "description": "Text"})
    await change_status(client, task["id"], "done")
    closed = await client.patch(url, json={"title": "Too late"})

    assert updated.status_code == HTTPStatus.OK
    assert (updated.json()["title"], updated.json()["description"]) == ("New", "Text")
    assert closed.status_code == HTTPStatus.CONFLICT
    assert closed.json()["code"] == "task_closed"


async def test_status_transitions(client: AsyncClient) -> None:
    task = await create_task(client, await create_project(client))

    started = await change_status(client, task["id"], "in_progress")
    back_to_todo = await change_status(client, task["id"], "todo")
    done = await change_status(client, task["id"], "done")

    assert started.status_code == HTTPStatus.OK
    assert started.json()["status"] == "in_progress"
    assert back_to_todo.status_code == HTTPStatus.CONFLICT
    assert back_to_todo.json()["code"] == "invalid_task_transition"
    assert back_to_todo.json()["details"] == {
        "task_id": task["id"],
        "current": "in_progress",
        "target": "todo",
    }
    assert done.json()["status"] == "done"


async def test_unknown_status_is_a_request_validation_error(
    client: AsyncClient,
) -> None:
    task = await create_task(client, await create_project(client))

    response = await change_status(client, task["id"], "paused")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "request_validation_error"


async def test_delete_a_task(client: AsyncClient) -> None:
    task = await create_task(client, await create_project(client))
    url = f"{TASKS_URL}/{task['id']}"

    deleted = await client.delete(url)
    fetched = await client.get(url)

    assert deleted.status_code == HTTPStatus.NO_CONTENT
    assert fetched.status_code == HTTPStatus.NOT_FOUND
    assert fetched.json()["code"] == "task_not_found"


async def test_list_tasks_filters_by_project_and_status(client: AsyncClient) -> None:
    website = await create_project(client, "Website")
    intranet = await create_project(client, "Intranet")
    first = await create_task(client, website, "First")
    await create_task(client, website, "Second")
    await create_task(client, intranet, "Other")
    await change_status(client, first["id"], "done")

    response = await client.get(
        TASKS_URL, params={"project_id": website, "status": "todo", "sort": "title"}
    )

    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert [item["title"] for item in body["items"]] == ["Second"]
    assert body["total"] == 1


async def test_archiving_a_project_cancels_its_open_tasks(client: AsyncClient) -> None:
    project_id = await create_project(client)
    todo = await create_task(client, project_id, "Todo")
    done = await create_task(client, project_id, "Done")
    await change_status(client, done["id"], "done")

    archived = await client.post(f"{PROJECTS_URL}/{project_id}/archive")
    todo_after = await client.get(f"{TASKS_URL}/{todo['id']}")
    done_after = await client.get(f"{TASKS_URL}/{done['id']}")

    assert archived.status_code == HTTPStatus.OK
    assert todo_after.json()["status"] == "cancelled"
    assert done_after.json()["status"] == "done"


async def test_deleting_a_project_deletes_only_its_tasks(client: AsyncClient) -> None:
    website = await create_project(client, "Website")
    intranet = await create_project(client, "Intranet")
    await create_task(client, website, "Website task")
    kept = await create_task(client, intranet, "Intranet task")

    deleted = await client.delete(f"{PROJECTS_URL}/{website}")
    remaining = await client.get(TASKS_URL)

    assert deleted.status_code == HTTPStatus.NO_CONTENT
    assert [item["id"] for item in remaining.json()["items"]] == [kept["id"]]
