"""Parent client — mirrors src/core/parentClient.ts from classcharts-api-js."""

from __future__ import annotations

import json
from typing import Any

import aiohttp

from .base_client import BaseClient
from .const import API_BASE_PARENT, BASE_URL
from .exceptions import ClassChartsAuthError, ClassChartsApiError
from .utils import parse_cookies


class ParentClient(BaseClient):
    """Async client for the ClassCharts parent API.

    Example::

        async with ParentClient("email@example.com", "password") as client:
            await client.login()
            homeworks = await client.get_homeworks_for_each_pupil()
    """

    def __init__(self, email: str, password: str) -> None:
        super().__init__(API_BASE_PARENT)
        self._email = email
        self._password = password
        self.pupils: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def login(self) -> None:
        """Authenticate with ClassCharts as a parent.

        Mirrors login() in parentClient.ts.
        """
        if not self._email:
            raise ClassChartsAuthError("Email not provided")
        if not self._password:
            raise ClassChartsAuthError("Password not provided")

        form = aiohttp.FormData()
        form.add_field("_method", "POST")
        form.add_field("email", self._email)
        form.add_field("logintype", "existing")
        form.add_field("password", self._password)
        form.add_field("recaptcha-token", "no-token-available")

        session = self._get_session()
        async with session.post(
            f"{BASE_URL}/parent/login",
            data=form,
            allow_redirects=False,
        ) as resp:
            if resp.status != 302 or "set-cookie" not in resp.headers:
                raise ClassChartsAuthError(
                    "Unauthenticated: ClassCharts didn't return authentication cookies"
                )
            cookie_headers: list[str] = resp.headers.getall("set-cookie", [])

        self.auth_cookies = cookie_headers
        # Find parent_session_credentials cookie by name
        cookies = parse_cookies(",".join(cookie_headers))
        raw_cred = cookies.get("parent_session_credentials")
        if not raw_cred:
            raise ClassChartsAuthError(
                "Unauthenticated: ClassCharts didn't return session credentials"
            )
        session_data = json.loads(raw_cred)
        self.session_id = session_data["session_id"]

        self.pupils = await self._fetch_pupils()
        if not self.pupils:
            raise ClassChartsApiError("Account has no pupils attached")
        self.student_id = self.pupils[0]["id"]

    # ------------------------------------------------------------------
    # Pupil management
    # ------------------------------------------------------------------

    async def _fetch_pupils(self) -> list[dict[str, Any]]:
        response = await self._make_authed_request(f"{self._api_base}/pupils")
        return response["data"]

    async def get_pupils(self) -> list[dict[str, Any]]:
        """Get a list of pupils connected to this parent account.

        Mirrors getPupils() in parentClient.ts.
        """
        self.pupils = await self._fetch_pupils()
        return self.pupils

    def select_pupil(self, pupil_id: int) -> None:
        """Select a pupil to use for subsequent API requests.

        Mirrors selectPupil() in parentClient.ts.
        """
        if not pupil_id:
            raise ClassChartsApiError("No pupil ID specified")
        for pupil in self.pupils:
            if pupil["id"] == pupil_id:
                self.student_id = pupil["id"]
                return
        raise ClassChartsApiError("No pupil with specified ID returned")

    # ------------------------------------------------------------------
    # Per-pupil homework helpers (new — not in JS lib)
    # ------------------------------------------------------------------

    async def get_homeworks_for_pupil(
        self,
        pupil_id: int,
        display_date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get homework for a specific pupil without permanently changing the selected pupil.

        Args:
            pupil_id: Pupil ID from self.pupils or get_pupils()
            display_date: "due_date" or "issue_date"
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        """
        previous_id = self.student_id
        try:
            self.select_pupil(pupil_id)
            return await self.get_homeworks(
                display_date=display_date,
                from_date=from_date,
                to_date=to_date,
            )
        finally:
            self.student_id = previous_id

    async def get_homeworks_for_each_pupil(
        self,
        display_date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        pupil_ids: list[int] | None = None,
    ) -> dict[int, dict[str, Any]]:
        """Get homework for multiple (or all) pupils.

        Args:
            display_date: "due_date" or "issue_date"
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            pupil_ids: Specific pupil IDs to fetch; defaults to all attached pupils
        """
        target_ids = pupil_ids if pupil_ids else [p["id"] for p in self.pupils]
        if not target_ids:
            raise ClassChartsApiError("No pupils available")

        known_ids = {p["id"] for p in self.pupils}
        invalid = [pid for pid in target_ids if pid not in known_ids]
        if invalid:
            raise ClassChartsApiError(
                f"No pupil with specified ID returned: {', '.join(str(i) for i in invalid)}"
            )

        previous_id = self.student_id
        result: dict[int, dict[str, Any]] = {}
        try:
            for pupil_id in target_ids:
                result[pupil_id] = await self.get_homeworks_for_pupil(
                    pupil_id,
                    display_date=display_date,
                    from_date=from_date,
                    to_date=to_date,
                )
        finally:
            self.student_id = previous_id
        return result

    # ------------------------------------------------------------------
    # Per-pupil convenience wrappers for other endpoints
    # ------------------------------------------------------------------

    async def get_lessons_for_pupil(self, pupil_id: int, date: str) -> dict[str, Any]:
        """Get timetable lessons for a specific pupil on a given date."""
        previous_id = self.student_id
        try:
            self.select_pupil(pupil_id)
            return await self.get_lessons(date)
        finally:
            self.student_id = previous_id

    async def get_behaviour_for_pupil(
        self,
        pupil_id: int,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get behaviour for a specific pupil."""
        previous_id = self.student_id
        try:
            self.select_pupil(pupil_id)
            return await self.get_behaviour(from_date=from_date, to_date=to_date)
        finally:
            self.student_id = previous_id

    async def get_activity_for_pupil(
        self,
        pupil_id: int,
        from_date: str,
        to_date: str,
    ) -> list[dict[str, Any]]:
        """Get full paginated activity for a specific pupil."""
        previous_id = self.student_id
        try:
            self.select_pupil(pupil_id)
            return await self.get_full_activity(from_date=from_date, to_date=to_date)
        finally:
            self.student_id = previous_id

    async def get_attendance_for_pupil(
        self,
        pupil_id: int,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get attendance for a specific pupil."""
        previous_id = self.student_id
        try:
            self.select_pupil(pupil_id)
            return await self.get_attendance(from_date=from_date, to_date=to_date)
        finally:
            self.student_id = previous_id

    # ------------------------------------------------------------------
    # Parent behaviour
    # ------------------------------------------------------------------

    async def get_parent_behaviours(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get parent-recorded behaviour points for the selected pupil."""
        params: dict[str, str] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._make_authed_request(
            f"{self._api_base}/parentbehaviours/{self.student_id}", params=params
        )

    async def add_parent_behaviour(
        self, reason_id: int, score: int, happened_at: str
    ) -> dict[str, Any]:
        """Add a parent behaviour point for the selected pupil."""
        form = aiohttp.FormData()
        form.add_field("reason_id", str(reason_id))
        form.add_field("score", str(score))
        form.add_field("happened_at", happened_at)
        return await self._make_authed_request(
            f"{self._api_base}/addparentbehaviour/{self.student_id}",
            method="POST",
            data=form,
        )

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    async def change_password(
        self, current_password: str, new_password: str
    ) -> dict[str, Any]:
        """Change the login password for the parent account.

        Mirrors changePassword() in parentClient.ts.
        """
        form = aiohttp.FormData()
        form.add_field("current", current_password)
        form.add_field("new", new_password)
        form.add_field("repeat", new_password)
        return await self._make_authed_request(
            f"{self._api_base}/password", method="POST", data=form
        )
