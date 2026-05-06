"""Tests for StudentClient — mirrors src/core/studentClient_test.ts."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiohttp import ClientSession

from classcharts_api import StudentClient
from classcharts_api.exceptions import ClassChartsAuthError


@pytest.mark.asyncio
async def test_raises_when_no_student_code():
    client = StudentClient("")
    with pytest.raises(ClassChartsAuthError, match="Student Code not provided"):
        await client.login()


@pytest.mark.asyncio
async def test_raises_with_invalid_student_code():
    """Simulate a non-302 response (invalid code)."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {}
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock(spec=ClientSession)
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.closed = False

    client = StudentClient("INVALID")
    client._session = mock_session

    with pytest.raises(ClassChartsAuthError, match="Unauthenticated"):
        await client.login()
