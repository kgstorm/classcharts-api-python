"""Base async client — shared logic for both ParentClient and StudentClient.

Mirrors src/core/baseClient.ts from classcharts-api-js.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

import aiohttp

from .const import PING_INTERVAL
from .exceptions import ClassChartsApiError


class BaseClient(ABC):
    """Shared async HTTP client for ClassCharts."""

    def __init__(self, api_base: str) -> None:
        self._api_base = api_base
        self.student_id: int = 0
        self.session_id: str = ""
        self.auth_cookies: list[str] = []
        self._last_ping: float = 0.0
        self._session: aiohttp.ClientSession | None = None

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "BaseClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    @abstractmethod
    async def login(self) -> None:
        """Authenticate with ClassCharts and store session credentials."""

    # ------------------------------------------------------------------
    # Session revalidation (ping)
    # ------------------------------------------------------------------

    async def get_new_session_id(self) -> None:
        """Revalidate the session ID.

        Called automatically when the session is older than PING_INTERVAL
        seconds, and immediately after login for student clients.
        Mirrors getNewSessionId() in baseClient.ts.
        """
        data = aiohttp.FormData()
        data.add_field("include_data", "true")
        response = await self._make_authed_request(
            f"{self._api_base}/ping",
            method="POST",
            data=data,
            revalidate_token=False,
        )
        self.session_id = response["meta"]["session_id"]
        self._last_ping = time.monotonic()

    # ------------------------------------------------------------------
    # Core request helper
    # ------------------------------------------------------------------

    async def _make_authed_request(
        self,
        url: str,
        method: str = "GET",
        data: Any = None,
        params: dict[str, str] | None = None,
        revalidate_token: bool = True,
    ) -> dict[str, Any]:
        """Make an authenticated request to the ClassCharts API.

        Mirrors makeAuthedRequest() in baseClient.ts.
        """
        if not self.session_id:
            raise ClassChartsApiError("No session ID — call login() first")

        if revalidate_token and self._last_ping:
            elapsed = time.monotonic() - self._last_ping
            if elapsed + 5 > PING_INTERVAL:
                await self.get_new_session_id()

        headers = {
            "Cookie": "; ".join(c.split(";")[0] for c in self.auth_cookies),
            "Authorization": f"Basic {self.session_id}",
            "User-Agent": "classcharts-api https://github.com/classchartsapi/classcharts-api-js",
        }

        session = self._get_session()
        async with session.request(
            method,
            url,
            headers=headers,
            data=data,
            params=params,
        ) as resp:
            try:
                payload: dict[str, Any] = await resp.json(content_type=None)
            except Exception as exc:
                text = await resp.text()
                raise ClassChartsApiError(
                    f"Error parsing JSON. Response: {text}"
                ) from exc

        if payload.get("success") == 0:
            raise ClassChartsApiError(payload.get("error", "Unknown API error"))

        return payload

    # ------------------------------------------------------------------
    # Shared endpoints
    # ------------------------------------------------------------------

    async def get_student_info(self) -> dict[str, Any]:
        """Get general information about the current student.

        Mirrors getStudentInfo() in baseClient.ts.
        """
        data = aiohttp.FormData()
        data.add_field("include_data", "true")
        return await self._make_authed_request(
            f"{self._api_base}/ping", method="POST", data=data
        )

    async def get_activity(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        last_id: str | None = None,
    ) -> dict[str, Any]:
        """Get the current student's activity (paginated).

        Mirrors getActivity() in baseClient.ts.
        """
        params: dict[str, str] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if last_id:
            params["last_id"] = last_id
        return await self._make_authed_request(
            f"{self._api_base}/activity/{self.student_id}", params=params
        )

    async def get_full_activity(
        self, from_date: str, to_date: str
    ) -> list[dict[str, Any]]:
        """Get all activity between two dates, handling pagination automatically.

        Mirrors getFullActivity() in baseClient.ts.
        """
        data: list[dict[str, Any]] = []
        prev_last: str | None = None
        while True:
            response = await self.get_activity(
                from_date=from_date, to_date=to_date, last_id=prev_last
            )
            fragment = response.get("data") or []
            if not fragment:
                break
            data.extend(fragment)
            prev_last = str(fragment[-1]["id"])
        return data

    async def get_behaviour(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get the current student's behaviour.

        Mirrors getBehaviour() in baseClient.ts.
        """
        params: dict[str, str] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._make_authed_request(
            f"{self._api_base}/behaviour/{self.student_id}", params=params
        )

    async def get_homeworks(
        self,
        display_date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get the current student's homeworks.

        Mirrors getHomeworks() in baseClient.ts.

        Args:
            display_date: "due_date" or "issue_date" (default: "issue_date")
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        """
        params: dict[str, str] = {}
        if display_date:
            params["display_date"] = display_date
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._make_authed_request(
            f"{self._api_base}/homeworks/{self.student_id}", params=params
        )

    async def get_lessons(self, date: str) -> dict[str, Any]:
        """Get the current student's lessons for a given date.

        Mirrors getLessons() in baseClient.ts.

        Args:
            date: Date in YYYY-MM-DD format
        """
        return await self._make_authed_request(
            f"{self._api_base}/timetable/{self.student_id}",
            params={"date": date},
        )

    async def get_badges(self) -> dict[str, Any]:
        """Get the current student's earned badges.

        Mirrors getBadges() in baseClient.ts.
        """
        return await self._make_authed_request(
            f"{self._api_base}/eventbadges/{self.student_id}"
        )

    async def get_announcements(self) -> dict[str, Any]:
        """Get the current student's announcements.

        Mirrors getAnnouncements() in baseClient.ts.
        """
        return await self._make_authed_request(
            f"{self._api_base}/announcements/{self.student_id}"
        )

    async def get_detentions(self) -> dict[str, Any]:
        """Get the current student's detentions.

        Mirrors getDetentions() in baseClient.ts.
        """
        return await self._make_authed_request(
            f"{self._api_base}/detentions/{self.student_id}"
        )

    async def get_attendance(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Get the current student's attendance.

        Mirrors getAttendance() in baseClient.ts.
        """
        params: dict[str, str] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._make_authed_request(
            f"{self._api_base}/attendance/{self.student_id}", params=params
        )

    async def get_pupil_fields(self) -> dict[str, Any]:
        """Get the current student's custom fields.

        Mirrors getPupilFields() in baseClient.ts.
        """
        return await self._make_authed_request(
            f"{self._api_base}/customfields/{self.student_id}"
        )

    async def get_classes(self) -> dict[str, Any]:
        """Get the classes the current student is enrolled in."""
        return await self._make_authed_request(
            f"{self._api_base}/classes/{self.student_id}"
        )

    async def get_academic_reports(self) -> dict[str, Any]:
        """List available academic reports for the current student."""
        return await self._make_authed_request(
            f"{self._api_base}/getacademicreports"
        )

    async def get_academic_report(self, report_id: int) -> dict[str, Any]:
        """Get a specific academic report by ID."""
        return await self._make_authed_request(
            f"{self._api_base}/getacademicreport/{report_id}"
        )

    async def get_report_cards(self) -> dict[str, Any]:
        """List on-report cards for the current student."""
        data = aiohttp.FormData()
        data.add_field("pupil_id", str(self.student_id))
        return await self._make_authed_request(
            f"{self._api_base}/getpupilreportcards", method="POST", data=data
        )

    async def get_report_card(self, report_card_id: int) -> dict[str, Any]:
        """Get a specific on-report card by ID."""
        return await self._make_authed_request(
            f"{self._api_base}/getpupilreportcard/{report_card_id}"
        )

    async def get_report_card_summary_comment(self, report_card_id: int) -> dict[str, Any]:
        """Get the summary comment for a specific on-report card."""
        return await self._make_authed_request(
            f"{self._api_base}/getpupilreportcardsummarycomment/{report_card_id}"
        )

    async def get_report_card_target(self, report_card_id: int) -> dict[str, Any]:
        """Get the target for a specific on-report card."""
        return await self._make_authed_request(
            f"{self._api_base}/getpupilreportcardtarget/{report_card_id}"
        )
