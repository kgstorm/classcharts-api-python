"""Live integration tests for ParentClient.

These tests hit the real ClassCharts API and are skipped unless
--live-classcharts is passed to pytest.
"""

from __future__ import annotations

import datetime as dt
import pytest

from classcharts_api import ParentClient


def _pupil_display_name(pupil: dict) -> str:
    """Return a readable pupil name from available API fields."""
    full_name = str(pupil.get("name", "")).strip()
    if full_name:
        return full_name

    first = str(
        pupil.get("forename")
        or pupil.get("firstname")
        or pupil.get("first_name")
        or ""
    ).strip()
    last = str(
        pupil.get("surname")
        or pupil.get("lastname")
        or pupil.get("last_name")
        or ""
    ).strip()
    combined = " ".join(part for part in (first, last) if part)
    return combined if combined else f"Pupil {pupil.get('id', 'unknown')}"


def _is_homework_todo(homework: dict) -> bool:
    """Return True when homework is not ticked, not completed, and due today or in the future."""
    status = homework.get("status") or {}
    if not isinstance(status, dict):
        return False

    ticked = str(status.get("ticked") or "").strip().lower()
    state = str(status.get("state") or "").strip().lower()
    due_date_str = str(homework.get("due_date") or "").strip()

    if ticked == "yes" or state == "completed":
        return False

    if not due_date_str:
        return False

    try:
        due_date = dt.date.fromisoformat(due_date_str[:10])
    except ValueError:
        return False

    return due_date >= dt.date.today()


def _class_display_name(class_item: dict) -> str:
    """Return a best-effort class name from varying API payload keys."""
    for key in ("name", "lesson_name", "class_name", "subject_name", "title"):
        value = class_item.get(key)
        if value:
            return str(value)
    return str(class_item.get("id", "unknown"))


def _lesson_display_name(lesson: dict) -> str:
    """Return best-effort lesson name from timetable payload keys."""
    for key in ("lesson_name", "name", "title", "subject_name", "subject"):
        value = lesson.get(key)
        if value:
            return str(value)
    return "(unnamed lesson)"


@pytest.mark.asyncio
async def test_live_behaviour_and_homework_for_each_pupil(
    live_creds: tuple[str, str],
    last_31_days: tuple[str, str],
) -> None:
    """Run live behaviour/homework summaries with one login for all pupils."""
    email, password = live_creds
    behaviour_from, behaviour_to = last_31_days
    homework_from = dt.date.today().isoformat()
    homework_to = None

    async with ParentClient(email, password) as client:
        await client.login()
        assert client.pupils, "No pupils returned after login"

        for pupil in client.pupils:
            pupil_id = int(pupil["id"])
            pupil_name = _pupil_display_name(pupil)

            behaviour = await client.get_behaviour_for_pupil(
                pupil_id,
                from_date=behaviour_from,
                to_date=behaviour_to,
            )
            assert behaviour.get("success") == 1
            timeline = (behaviour.get("data") or {}).get("timeline", [])
            assert isinstance(timeline, list)

            total_positive = sum(int(point.get("positive", 0)) for point in timeline)
            total_negative = sum(int(point.get("negative", 0)) for point in timeline)
            net_points = total_positive - total_negative
            print(
                f"{pupil_name}: net={net_points} "
                f"(+{total_positive} / -{total_negative})"
            )

            homework_resp = await client.get_homeworks_for_pupil(
                pupil_id,
                display_date="due_date",
                from_date=homework_from,
                to_date=homework_to,
            )
            assert homework_resp.get("success") == 1
            homeworks = homework_resp.get("data") or []
            assert isinstance(homeworks, list)

            today = dt.date.today()
            due_today_or_future = []
            for hw in homeworks:
                due_date_str = str(hw.get("due_date") or "").strip()
                try:
                    due_date = dt.date.fromisoformat(due_date_str[:10])
                except ValueError:
                    continue
                if due_date >= today:
                    due_today_or_future.append(hw)

            recent = sorted(
                due_today_or_future,
                key=lambda hw: str(hw.get("due_date") or ""),
                reverse=True,
            )[:10]

            print(
                f"{pupil_name}: latest {len(recent)} of {len(due_today_or_future)} "
                "homeworks due today or later"
            )
            for index, homework in enumerate(recent, start=1):
                status = homework.get("status") or {}
                print(
                    f"  {index:2}. due={homework.get('due_date')} "
                    f"ticked={status.get('ticked')} "
                    f"state={str(status.get('state') or 'null'):<12} "
                    f"subject={str(homework.get('subject') or homework.get('lesson') or ''):<20} "
                    f"title={homework.get('title')!r}"
                )

            previous_id = client.student_id
            try:
                client.select_pupil(pupil_id)
                classes_resp = await client.get_classes()
            finally:
                client.student_id = previous_id

            assert classes_resp.get("success") == 1
            classes_data = classes_resp.get("data") or []
            if not isinstance(classes_data, list):
                classes_data = [classes_data]

            print(f"{pupil_name}: classes={len(classes_data)}")
            for index, class_item in enumerate(classes_data[:10], start=1):
                if not isinstance(class_item, dict):
                    print(f"  {index:2}. {class_item}")
                    continue
                print(
                    f"  {index:2}. class={_class_display_name(class_item)!r} "
                    f"teacher={class_item.get('teacher_name') or class_item.get('teacher')!r} "
                    f"room={class_item.get('room_name') or class_item.get('room')!r}"
                )

            print(f"{pupil_name}: timetable next 7 days")
            for offset in range(7):
                day = dt.date.today() + dt.timedelta(days=offset)
                day_iso = day.isoformat()
                lessons_resp = await client.get_lessons_for_pupil(pupil_id, day_iso)
                assert lessons_resp.get("success") == 1

                lessons = lessons_resp.get("data") or []
                if not isinstance(lessons, list):
                    lessons = [lessons]

                print(f"  {day_iso}: lessons={len(lessons)}")
                for index, lesson in enumerate(lessons[:10], start=1):
                    if not isinstance(lesson, dict):
                        print(f"    {index:2}. {lesson}")
                        continue
                    print(
                        f"    {index:2}. lesson={_lesson_display_name(lesson)!r} "
                        f"period={lesson.get('period_name') or lesson.get('period')!r} "
                        f"start={lesson.get('start_time')!r} "
                        f"end={lesson.get('end_time')!r} "
                        f"teacher={lesson.get('teacher_name')!r} "
                        f"room={lesson.get('room_name')!r}"
                    )
