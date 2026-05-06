"""Tests for ParentClient — mirrors src/core/parentClient_test.ts."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientSession

from classcharts_api import ParentClient
from classcharts_api.exceptions import ClassChartsAuthError, ClassChartsApiError


# ---------------------------------------------------------------------------
# Auth / login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_raises_when_no_email():
    client = ParentClient("", "password")
    with pytest.raises(ClassChartsAuthError, match="Email not provided"):
        await client.login()


@pytest.mark.asyncio
async def test_raises_when_no_password():
    client = ParentClient("email@example.com", "")
    with pytest.raises(ClassChartsAuthError, match="Password not provided"):
        await client.login()


@pytest.mark.asyncio
async def test_raises_with_invalid_credentials():
    """Simulate a non-302 response (invalid credentials)."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {}
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock(spec=ClientSession)
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.closed = False

    client = ParentClient("invalid@example.com", "invalid")
    client._session = mock_session

    with pytest.raises(ClassChartsAuthError, match="Unauthenticated"):
        await client.login()


# ---------------------------------------------------------------------------
# get_homeworks_for_pupil
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_homeworks_for_pupil_uses_correct_pupil_id():
    client = ParentClient("email@example.com", "password")
    client.pupils = [{"id": 1}, {"id": 2}]
    client.student_id = 1
    client.session_id = "fake_session"
    client._last_ping = float("inf")  # prevent revalidation

    requested_ids: list[int] = []

    async def fake_get_homeworks(**kwargs):
        requested_ids.append(client.student_id)
        return {"success": 1, "data": [], "meta": {}}

    client.get_homeworks = fake_get_homeworks

    await client.get_homeworks_for_pupil(2)

    assert requested_ids == [2]
    assert client.student_id == 1  # restored


@pytest.mark.asyncio
async def test_get_homeworks_for_pupil_restores_id_on_error():
    client = ParentClient("email@example.com", "password")
    client.pupils = [{"id": 10}, {"id": 20}]
    client.student_id = 10
    client.session_id = "fake_session"

    async def failing_get_homeworks(**kwargs):
        raise ClassChartsApiError("Network error")

    client.get_homeworks = failing_get_homeworks

    with pytest.raises(ClassChartsApiError):
        await client.get_homeworks_for_pupil(20)

    assert client.student_id == 10  # still restored


# ---------------------------------------------------------------------------
# get_homeworks_for_each_pupil
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_homeworks_for_each_pupil_fetches_all_pupils():
    client = ParentClient("email@example.com", "password")
    client.pupils = [{"id": 10}, {"id": 20}, {"id": 30}]
    client.student_id = 20
    client.session_id = "fake_session"

    requested_ids: list[int] = []

    async def fake_get_homeworks_for_pupil(pupil_id, **kwargs):
        requested_ids.append(pupil_id)
        return {"success": 1, "data": [], "meta": {}}

    client.get_homeworks_for_pupil = fake_get_homeworks_for_pupil

    result = await client.get_homeworks_for_each_pupil()

    assert requested_ids == [10, 20, 30]
    assert set(result.keys()) == {10, 20, 30}
    assert client.student_id == 20  # restored


@pytest.mark.asyncio
async def test_get_homeworks_for_each_pupil_rejects_unknown_ids():
    client = ParentClient("email@example.com", "password")
    client.pupils = [{"id": 1}, {"id": 2}]
    client.session_id = "fake_session"

    with pytest.raises(ClassChartsApiError, match="99"):
        await client.get_homeworks_for_each_pupil(pupil_ids=[2, 99])


@pytest.mark.asyncio
async def test_get_homeworks_for_each_pupil_raises_when_no_pupils():
    client = ParentClient("email@example.com", "password")
    client.pupils = []
    client.session_id = "fake_session"

    with pytest.raises(ClassChartsApiError, match="No pupils available"):
        await client.get_homeworks_for_each_pupil()


# ---------------------------------------------------------------------------
# select_pupil
# ---------------------------------------------------------------------------

def test_select_pupil_sets_student_id():
    client = ParentClient("email@example.com", "password")
    client.pupils = [{"id": 100}, {"id": 200}]
    client.select_pupil(200)
    assert client.student_id == 200


def test_select_pupil_raises_on_unknown_id():
    client = ParentClient("email@example.com", "password")
    client.pupils = [{"id": 100}]
    with pytest.raises(ClassChartsApiError, match="No pupil with specified ID"):
        client.select_pupil(999)


def test_select_pupil_raises_with_no_id():
    client = ParentClient("email@example.com", "password")
    with pytest.raises(ClassChartsApiError, match="No pupil ID specified"):
        client.select_pupil(0)
