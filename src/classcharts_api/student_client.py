"""Student client — mirrors src/core/studentClient.ts from classcharts-api-js."""

from __future__ import annotations

import json
from typing import Any

import aiohttp

from .base_client import BaseClient
from .const import API_BASE_STUDENT, BASE_URL
from .exceptions import ClassChartsAuthError, ClassChartsApiError
from .utils import parse_cookies


class StudentClient(BaseClient):
    """Async client for the ClassCharts student API.

    Example::

        async with StudentClient("STUDENT_CODE", "01/01/2000") as client:
            await client.login()
            homeworks = await client.get_homeworks()
    """

    def __init__(self, student_code: str, date_of_birth: str = "") -> None:
        super().__init__(API_BASE_STUDENT)
        self._student_code = student_code
        self._date_of_birth = date_of_birth

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def login(self) -> None:
        """Authenticate with ClassCharts as a student.

        Mirrors login() in studentClient.ts.
        """
        if not self._student_code:
            raise ClassChartsAuthError("Student Code not provided")

        form = aiohttp.FormData()
        form.add_field("_method", "POST")
        form.add_field("code", self._student_code.upper())
        form.add_field("dob", self._date_of_birth)
        form.add_field("remember_me", "1")
        form.add_field("recaptcha-token", "no-token-available")

        session = self._get_session()
        async with session.post(
            f"{BASE_URL}/student/login",
            data=form,
            allow_redirects=False,
        ) as resp:
            if resp.status != 302 or "set-cookie" not in resp.headers:
                raise ClassChartsAuthError(
                    "Unauthenticated: ClassCharts didn't return authentication cookies"
                )
            cookie_headers: list[str] = resp.headers.getall("set-cookie", [])

        self.auth_cookies = cookie_headers
        cookies = parse_cookies(",".join(cookie_headers))
        raw_cred = cookies.get("student_session_credentials")
        if not raw_cred:
            raise ClassChartsAuthError(
                "Unauthenticated: ClassCharts didn't return session credentials"
            )
        session_data = json.loads(raw_cred)
        self.session_id = session_data["session_id"]

        await self.get_new_session_id()
        user_info = await self.get_student_info()
        self.student_id = user_info["data"]["user"]["id"]

    # ------------------------------------------------------------------
    # Student-only endpoints
    # ------------------------------------------------------------------

    async def get_rewards(self) -> dict[str, Any]:
        """Get available items in the student's rewards shop.

        Mirrors getRewards() in studentClient.ts.
        """
        return await self._make_authed_request(
            f"{self._api_base}/rewards/{self.student_id}"
        )

    async def purchase_reward(self, item_id: int) -> dict[str, Any]:
        """Purchase a reward item from the student's rewards shop.

        Mirrors purchaseReward() in studentClient.ts.
        """
        form = aiohttp.FormData()
        form.add_field("pupil_id", str(self.student_id))
        return await self._make_authed_request(
            f"{self._api_base}/purchase/{item_id}", method="POST", data=form
        )

    async def get_student_code(self, date_of_birth: str) -> dict[str, Any]:
        """Get the student's ClassCharts code.

        Mirrors getStudentCode() in studentClient.ts.

        Args:
            date_of_birth: Date of birth in YYYY-MM-DD format
        """
        form = aiohttp.FormData()
        form.add_field("date", date_of_birth)
        return await self._make_authed_request(
            f"{self._api_base}/getcode", method="POST", data=form
        )

    async def tick_homework(self, homework_status_id: int) -> dict[str, Any]:
        """Mark a homework item as ticked/seen.

        Args:
            homework_status_id: The status ID from Homework.status.id
        """
        return await self._make_authed_request(
            f"{self._api_base}/homeworkticked/{homework_status_id}", method="GET"
        )
