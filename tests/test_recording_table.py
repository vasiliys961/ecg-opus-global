from __future__ import annotations

import math

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from ecg_engine.ecgfounder import LEADS
from ecg_engine.raw_extractor import RAW_TO_531_STATUS
from ecg_engine.recording_table import RecordingTableError, to_csv


def _columns() -> list[list[float]]:
    return [[float(lead) - 0.115 + index / 10 for index in range(4)] for lead in range(12)]


def test_table_matches_the_csv_contract():
    text = to_csv(_columns())
    header, *rows = [line for line in text.splitlines() if line]
    assert header.split(",") == list(LEADS)
    assert len(rows) == 4
    parsed = [[float(cell) for cell in row.split(",")] for row in rows]
    np.testing.assert_allclose(np.array(parsed).T, _columns())


def test_table_rejects_bytes_and_a_short_grid():
    with pytest.raises(RecordingTableError, match="не байты"):
        to_csv(b"\x55\xaa\x00")
    with pytest.raises(RecordingTableError, match="12 отведений"):
        to_csv(_columns()[:11])
    broken = _columns()
    broken[3] = broken[3][:-1]
    with pytest.raises(RecordingTableError, match="одно и то же число"):
        to_csv(broken)
    nan_columns = _columns()
    nan_columns[0][0] = math.nan
    with pytest.raises(RecordingTableError, match="NaN"):
        to_csv(nan_columns)


def test_assembled_table_uses_the_existing_csv_route(monkeypatch):
    monkeypatch.setattr(
        "backend.app.predict_signal",
        lambda signal, lead_names, sampling_rate: {
            "model": "ECGFounder",
            "scores": [{"label": "SINUS RHYTHM", "score": 0.2}],
            "note": "проверка кабельной таблицы",
        },
    )
    payload = to_csv([[0.0] * 5000 for _ in LEADS])
    with TestClient(app) as client:
        response = client.post(
            "/api/ecg/signal/csv",
            files={"file": ("cable.csv", payload, "text/csv")},
            data={"sampling_rate": "500"},
        )
    assert response.status_code == 200
    assert response.json()["model"] == "ECGFounder"
    assert RAW_TO_531_STATUS == "NOT_PROVEN"


def test_page_has_no_cable_module():
    with TestClient(app) as client:
        page = client.get("/")
        cable = client.get("/cable.js")
        guide = client.get("/ecg-connect.html")
    assert page.status_code == 200
    assert 'id="panel-signal"' not in page.text
    assert 'id="score-cable"' not in page.text
    assert 'src="/cable.js"' not in page.text
    assert "Инструкция по подключению ЭКГ" not in page.text
    assert cable.status_code == 404
    assert guide.status_code == 404
