import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_PAYLOAD_BYTES = 20 * 1024


class OkResponse(BaseModel):
    ok: bool = True
    ignored: str | None = None


class TrackRequest(BaseModel):
    project_key: str = Field(..., max_length=64)
    event_type: str = Field(..., max_length=64)
    path: str = Field(..., max_length=2048)
    title: str | None = Field(default=None, max_length=512)
    referrer: str | None = Field(default=None, max_length=2048)
    session_id: str | None = Field(default=None, max_length=128)
    visitor_id: str | None = Field(default=None, max_length=128)
    screen_width: int | None = None
    screen_height: int | None = None
    language: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] | None = None

    @field_validator("payload")
    @classmethod
    def validate_payload_size(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ValueError(f"payload exceeds maximum size of {MAX_PAYLOAD_BYTES} bytes")
        return value


class PushKeys(BaseModel):
    p256dh: str = Field(..., max_length=512)
    auth: str = Field(..., max_length=256)


class PushSubscribeRequest(BaseModel):
    project_key: str = Field(..., max_length=64)
    endpoint: str = Field(..., max_length=2048)
    keys: PushKeys


class PushSendRequest(BaseModel):
    title: str = Field(..., max_length=512)
    body: str = Field(..., max_length=2048)
    url: str | None = Field(default=None, max_length=2048)


class TopItem(BaseModel):
    value: str
    count: int


class RecentEvent(BaseModel):
    id: int
    event_type: str
    path: str
    title: str | None
    referrer: str | None
    visitor_id: str | None
    session_id: str | None
    created_at: datetime


class ProjectStats(BaseModel):
    project_key: str
    project_name: str
    total_events: int
    unique_visitors: int
    events_today: int
    events_last_7_days: int
    active_push_subscriptions: int
    top_paths: list[TopItem]
    top_referrers: list[TopItem]
    events_by_type: list[TopItem]
    recent_events: list[RecentEvent]


class PushSendResult(BaseModel):
    ok: bool
    sent: int
    failed: int
    deactivated: int


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
    time: str
