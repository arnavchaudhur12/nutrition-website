from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import uuid4


@dataclass(slots=True)
class VisitorPresenceService:
    ttl_seconds: int = 45
    _sessions: dict[str, datetime] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def connect(self) -> dict[str, object]:
        with self._lock:
            self._prune_locked()
            session_id = uuid4().hex
            self._sessions[session_id] = self._expires_at()
            return {"session_id": session_id, "active_visitors": len(self._sessions)}

    def heartbeat(self, session_id: str) -> dict[str, object]:
        with self._lock:
            self._prune_locked()
            self._sessions[session_id] = self._expires_at()
            return {"session_id": session_id, "active_visitors": len(self._sessions)}

    def disconnect(self, session_id: str) -> dict[str, int]:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._prune_locked()
            return {"active_visitors": len(self._sessions)}

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            self._prune_locked()
            return {"active_visitors": len(self._sessions)}

    def _prune_locked(self) -> None:
        now = datetime.now(UTC)
        expired_sessions = [
            session_id for session_id, expires_at in self._sessions.items() if expires_at <= now
        ]
        for session_id in expired_sessions:
            self._sessions.pop(session_id, None)

    def _expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
