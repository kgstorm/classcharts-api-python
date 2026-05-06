"""Dataclass models ported from types.ts."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Student / Pupil
# ---------------------------------------------------------------------------

@dataclass
class Student:
    id: int
    name: str
    first_name: str
    last_name: str
    avatar_url: str
    display_behaviour: bool
    display_parent_behaviour: bool
    display_homework: bool
    display_rewards: bool
    display_detentions: bool
    display_report_cards: bool
    display_classes: bool
    display_announcements: bool
    display_attendance: bool
    display_attendance_type: str
    display_attendance_percentage: bool
    display_activity: bool
    display_mental_health: bool
    display_timetable: bool
    is_disabled: bool
    display_two_way_communications: bool
    display_absences: bool
    can_upload_attachments: bool | None
    display_event_badges: bool
    display_avatars: bool
    display_concern_submission: bool
    display_custom_fields: bool
    pupil_concerns_help_text: str
    allow_pupils_add_timetable_notes: bool
    announcements_count: int
    messages_count: int
    pusher_channel_name: str
    has_birthday: bool
    has_new_survey: bool
    survey_id: int | None
    detention_alias_plural_uc: str


@dataclass
class Pupil(Student):
    school_name: str = ""
    school_logo: str = ""
    timezone: str = ""
    display_covid_tests: bool = False
    can_record_covid_tests: bool = False
    detention_yes_count: int = 0
    detention_no_count: int = 0
    detention_pending_count: int = 0
    detention_upscaled_count: int = 0
    homework_todo_count: int = 0
    homework_late_count: int = 0
    homework_not_completed_count: int = 0
    homework_excused_count: int = 0
    homework_completed_count: int = 0
    homework_submitted_count: int = 0


# ---------------------------------------------------------------------------
# Student info response
# ---------------------------------------------------------------------------

@dataclass
class GetStudentInfoData:
    user: Student


@dataclass
class GetStudentInfoMeta:
    session_id: str
    version: str = ""


@dataclass
class GetStudentInfoResponse:
    data: GetStudentInfoData
    meta: GetStudentInfoMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------

@dataclass
class BehaviourTimelinePoint:
    positive: int
    negative: int
    name: str
    start: str
    end: str


@dataclass
class BehaviourData:
    timeline: list[BehaviourTimelinePoint]
    positive_reasons: dict[str, int]
    negative_reasons: dict[str, int]
    other_positive: list[str]
    other_negative: list[str]
    other_positive_count: list[dict[str, int]]
    other_negative_count: list[dict[str, int]]


@dataclass
class BehaviourMeta:
    start_date: str
    end_date: str
    step_size: str


@dataclass
class BehaviourResponse:
    data: BehaviourData
    meta: BehaviourMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------

@dataclass
class ActivityPointStyle:
    border_color: str | None
    custom_class: str | None


@dataclass
class ActivityPoint:
    id: int
    type: str
    polarity: str | None
    reason: str
    score: int
    timestamp: str
    timestamp_custom_time: str | None
    style: ActivityPointStyle
    pupil_name: str
    lesson_name: str | None
    teacher_name: str | None
    room_name: str | None
    note: str | None
    _can_delete: bool
    badges: str
    detention_date: str | None
    detention_time: str | None
    detention_location: str | None
    detention_type: str | None


@dataclass
class ActivityMeta:
    start_date: str
    end_date: str
    last_id: int | bool
    step_size: str
    detention_alias_uc: str


@dataclass
class ActivityResponse:
    data: list[ActivityPoint]
    meta: ActivityMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Homework
# ---------------------------------------------------------------------------

@dataclass
class TeacherValidatedHomeworkAttachment:
    id: int
    file_name: str
    file: str
    validated_file: str


@dataclass
class TeacherValidatedHomeworkLink:
    link: str
    validated_link: str


@dataclass
class StudentHomeworkAttachment:
    id: int
    file_name: str
    file: str
    validated_file: str
    teacher_note: str
    teacher_homework_attachments: list[TeacherValidatedHomeworkAttachment]
    can_delete: bool


@dataclass
class HomeworkStatus:
    id: int
    state: str | None  # "not_completed" | "late" | "completed" | None
    mark: str | None
    mark_relative: int
    ticked: str  # "yes" | "no"
    allow_attachments: bool
    allow_marking_completed: bool
    first_seen_date: str | None
    last_seen_date: str | None
    attachments: list[StudentHomeworkAttachment]
    has_feedback: bool


@dataclass
class Homework:
    lesson: str
    subject: str | None
    teacher: str
    homework_type: str
    id: int
    title: str
    meta_title: str
    description: str
    issue_date: str
    due_date: str
    completion_time_unit: str
    completion_time_value: str
    publish_time: str
    status: HomeworkStatus
    validated_links: list[TeacherValidatedHomeworkLink]
    validated_attachments: list[TeacherValidatedHomeworkAttachment]


@dataclass
class HomeworksMeta:
    start_date: str
    end_date: str
    display_type: str
    max_files_allowed: int
    allowed_file_types: list[str]
    this_week_due_count: int
    this_week_outstanding_count: int
    this_week_completed_count: int
    allow_attachments: bool
    display_marks: bool


@dataclass
class HomeworksResponse:
    data: list[Homework]
    meta: HomeworksMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Lessons / Timetable
# ---------------------------------------------------------------------------

@dataclass
class Lesson:
    teacher_name: str
    teacher_id: str
    lesson_name: str
    subject_name: str
    is_alternative_lesson: bool
    period_name: str
    period_number: str
    room_name: str
    date: str
    start_time: str
    end_time: str
    key: int
    note_abstract: str
    note: str
    pupil_note_abstract: str
    pupil_note: str
    pupil_note_raw: str
    is_break: bool = False


@dataclass
class PeriodMeta:
    number: str
    start_time: str
    end_time: str


@dataclass
class LessonsMeta:
    dates: list[str]
    timetable_dates: list[str]
    periods: list[PeriodMeta]
    start_time: str
    end_time: str


@dataclass
class LessonsResponse:
    data: list[Lesson]
    meta: LessonsMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

@dataclass
class LessonPupilBehaviour:
    reason: str
    score: int
    icon: str
    polarity: str
    timestamp: str
    teacher: dict[str, str]


@dataclass
class PupilEvent:
    timestamp: str
    lesson_pupil_behaviour: LessonPupilBehaviour
    event: dict[str, str]


@dataclass
class Badge:
    id: int
    name: str
    icon: str
    colour: str
    created_date: str
    pupil_badges: list[dict[str, Any]]
    icon_url: str


@dataclass
class BadgesResponse:
    data: list[Badge]
    meta: list
    success: int = 1


# ---------------------------------------------------------------------------
# Detentions
# ---------------------------------------------------------------------------

@dataclass
class Detention:
    id: int
    attended: str  # "yes" | "no" | "upscaled" | "pending"
    date: str | None
    length: int | None
    location: str | None
    notes: str | None
    time: str | None
    pupil: dict[str, Any]
    lesson: dict[str, Any] | None
    lesson_pupil_behaviour: dict[str, Any]
    teacher: dict[str, Any] | None
    detention_type: dict[str, Any] | None


@dataclass
class DetentionsMeta:
    detention_alias_plural: str


@dataclass
class DetentionsResponse:
    data: list[Detention]
    meta: DetentionsMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

@dataclass
class AnnouncementConsent:
    consent_given: str  # "yes" | "no"
    comment: str | None
    parent_name: str


@dataclass
class AnnouncementPupilConsent:
    pupil: dict[str, str]
    can_change_consent: bool
    consent: AnnouncementConsent | None


@dataclass
class Announcement:
    id: int
    title: str
    description: str | None
    school_name: str
    teacher_name: str
    school_logo: str | None
    sticky: str
    state: str | None
    timestamp: str
    attachments: list[dict[str, str]]
    for_pupils: list[str]
    comment_visibility: str
    allow_comments: str
    allow_reactions: str
    allow_consent: str
    priority_pinned: str
    requires_consent: str
    can_change_consent: bool
    consent: AnnouncementConsent | None
    pupil_consents: list[AnnouncementPupilConsent]


@dataclass
class AnnouncementsResponse:
    data: list[Announcement]
    meta: list
    success: int = 1


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

@dataclass
class AttendancePeriod:
    code: str
    status: str  # "yes"|"present"|"ignore"|"no"|"absent"|"excused"|"late"
    late_minutes: int | str
    lesson_name: str | None = None
    room_name: str | None = None


@dataclass
class AttendanceMeta:
    dates: list[str]
    sessions: list[str]
    start_date: str
    end_date: str
    percentage: str
    percentage_singe_august: str


@dataclass
class AttendanceResponse:
    data: dict[str, dict[str, AttendancePeriod]]
    meta: AttendanceMeta
    success: int = 1


# ---------------------------------------------------------------------------
# Pupil fields (custom fields)
# ---------------------------------------------------------------------------

@dataclass
class PupilField:
    id: int
    name: str
    graphic: str
    value: str


@dataclass
class PupilFieldsData:
    note: str
    fields: list[PupilField]


@dataclass
class PupilFieldsResponse:
    data: PupilFieldsData
    meta: list
    success: int = 1


# ---------------------------------------------------------------------------
# Rewards (student only)
# ---------------------------------------------------------------------------

@dataclass
class Reward:
    id: int
    name: str
    description: str
    photo: str
    price: int
    stock_control: bool
    stock: int
    can_purchase: bool
    unable_to_purchase_reason: str
    once_per_pupil: bool
    purchased: bool
    purchased_count: str | int
    price_balance_difference: int


@dataclass
class RewardsMeta:
    pupil_score_balance: int


@dataclass
class RewardsResponse:
    data: list[Reward]
    meta: RewardsMeta
    success: int = 1


@dataclass
class RewardPurchaseData:
    single_purchase: str  # "yes" | "no"
    order_id: int
    balance: int


@dataclass
class RewardPurchaseResponse:
    data: RewardPurchaseData
    meta: list
    success: int = 1


# ---------------------------------------------------------------------------
# Change password / misc
# ---------------------------------------------------------------------------

@dataclass
class ChangePasswordResponse:
    data: list
    meta: list
    success: int = 1


@dataclass
class GetStudentCodeData:
    code: str


@dataclass
class GetStudentCodeResponse:
    data: GetStudentCodeData
    meta: list
    success: int = 1
