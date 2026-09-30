"""Сессия смартфона и компьютера.

Карточка пациента живёт только в этой сессии. В разбор модели она не передаётся.
"""

from __future__ import annotations

import re
import secrets
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

TTL_SECONDS = 12 * 60 * 60
MAX_FILE_BYTES = 20_000_000
SEX_VALUES = {"", "муж.", "жен."}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class BridgeError(ValueError):
    """Сессия или посылка телефона не принята."""


@dataclass
class BridgeEvent:
    id: int
    kind: str
    filename: str = ""
    mime: str = ""
    path: str = ""
    name: str = ""
    year: str = ""
    sex: str = ""
    study_date: str = ""


@dataclass
class _Session:
    token: str
    expires_at: float
    next_id: int = 1
    events: list[BridgeEvent] = field(default_factory=list)


class BridgeStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, _Session] = {}
        self._dir = Path(tempfile.mkdtemp(prefix="ecg-bridge-"))

    def reset(self) -> None:
        with self._lock:
            self._sessions.clear()

    def create(self) -> str:
        token = secrets.token_urlsafe(18)
        with self._lock:
            self._drop_expired()
            self._sessions[token] = _Session(token, time.time() + TTL_SECONDS)
        return token

    def add_patient(self, token: str, name: str, year: str, sex: str, study_date: str) -> int | None:
        fields = _patient_fields(name, year, sex, study_date)
        if not any(fields.values()):
            return None
        with self._lock:
            session = self._open(token)
            event = BridgeEvent(id=session.next_id, kind="patient", **fields)
            session.next_id += 1
            session.events.append(event)
            return event.id

    def add_file(self, token: str, filename: str, mime: str, payload: bytes) -> int:
        if not payload:
            raise BridgeError("С телефона пришёл пустой файл.")
        if len(payload) > MAX_FILE_BYTES:
            raise BridgeError("Файл с телефона больше 20 МБ.")
        safe_name = _filename(filename)
        with self._lock:
            session = self._open(token)
            event_id = session.next_id
            session.next_id += 1
            path = self._dir / f"{token}-{event_id}"
            path.write_bytes(payload)
            session.events.append(
                BridgeEvent(
                    id=event_id,
                    kind="file",
                    filename=safe_name,
                    mime=(mime or "application/octet-stream")[:80],
                    path=str(path),
                )
            )
            return event_id

    def since(self, token: str, since_id: int) -> list[dict[str, str | int]]:
        with self._lock:
            session = self._open(token)
            return [_public(event) for event in session.events if event.id > since_id]

    def read_file(self, token: str, event_id: int) -> tuple[bytes, str, str]:
        with self._lock:
            session = self._open(token)
            event = next((item for item in session.events if item.id == event_id), None)
            if event is None or event.kind != "file" or not event.path:
                raise BridgeError("Файл этой сессии не найден.")
            path = Path(event.path)
            payload = path.read_bytes()
            return payload, event.filename, event.mime

    def _open(self, token: str) -> _Session:
        self._drop_expired()
        session = self._sessions.get(token)
        if session is None:
            raise BridgeError("Сессия телефона не найдена. Обновите код на компьютере.")
        session.expires_at = time.time() + TTL_SECONDS
        return session

    def _drop_expired(self) -> None:
        now = time.time()
        for token in [item for item, session in self._sessions.items() if session.expires_at <= now]:
            del self._sessions[token]


def _patient_fields(name: str, year: str, sex: str, study_date: str) -> dict[str, str]:
    clean_name = " ".join(name.split())[:120]
    clean_year = year.strip()
    clean_sex = sex.strip()
    clean_date = study_date.strip()
    if clean_year and (not clean_year.isdigit() or not 1900 <= int(clean_year) <= 2100):
        raise BridgeError("Год рождения с телефона не разобран.")
    if clean_sex not in SEX_VALUES:
        raise BridgeError("Пол с телефона не разобран.")
    if clean_date and not DATE_RE.fullmatch(clean_date):
        raise BridgeError("Дата снятия ЭКГ с телефона не разобрана.")
    return {"name": clean_name, "year": clean_year, "sex": clean_sex, "study_date": clean_date}


def _filename(raw: str) -> str:
    name = Path(raw or "ecg").name.replace("\x00", "")
    name = re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "ecg"
    return name[:120]


def _public(event: BridgeEvent) -> dict[str, str | int]:
    if event.kind == "file":
        return {"id": event.id, "kind": "file", "filename": event.filename, "mime": event.mime}
    return {
        "id": event.id,
        "kind": "patient",
        "name": event.name,
        "year": event.year,
        "sex": event.sex,
        "study_date": event.study_date,
    }


bridge = BridgeStore()
