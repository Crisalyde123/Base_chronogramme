from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "chronogram_pipeline" / "data" / "control"
MAPPING_LOG = BASE_DIR / "chronogram_pipeline" / "config" / "mappings_log.xlsx"
DB_PATH = BASE_DIR / "chronogram_pipeline" / "output" / "databases" / "chronogrammes.db"
REPORT_PATH = LOG_DIR / "monitoring_log.md"


def _load_chrono_id(log_file: Path) -> int | None:
    """Return the chrono_id recorded in *log_file* summary."""
    try:
        with log_file.open() as fh:
            for line in fh:
                data = json.loads(line)
                if data.get("event") == "SUMMARY":
                    for step in data.get("steps", []):
                        if step.get("name") == "INSERT_METADATA":
                            return int(step.get("chrono_id"))
    except Exception:
        pass
    return None


def _compute_completeness(conn: sqlite3.Connection, chrono_id: str) -> float:
    df = pd.read_sql(
        "SELECT * FROM Injects WHERE id_chronogramme = ?",
        conn,
        params=(chrono_id,),
    )
    if df.empty:
        return 0.0
    cols = [c for c in df.columns if c not in {"id_chronogramme"}]
    filled = df[cols].notna().sum().sum()
    total = len(df) * len(cols)
    return float(filled) / float(total) if total else 0.0


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def generate_report() -> None:
    mapping_df = pd.read_excel(MAPPING_LOG) if MAPPING_LOG.exists() else pd.DataFrame()
    records: Dict[str, Any] = {}
    with sqlite3.connect(DB_PATH) as conn:
        for log in sorted(LOG_DIR.glob("run_*.log")):
            chrono_id = _load_chrono_id(log)
            if chrono_id is None:
                continue
            subset = mapping_df[mapping_df["id_chronogramme"] == chrono_id]
            total = len(subset)
            auto_count = (subset["methode"] == "règle").sum()
            ia_count = (subset["methode"] == "IA").sum()
            unresolved = (
                subset["champ_standard"].isna().sum()
                + (subset["champ_standard"] == "").sum()
            )
            auto_rate = auto_count / total if total else 0.0
            ia_rate = ia_count / total if total else 0.0
            unresolved_rate = unresolved / total if total else 0.0
            completeness = _compute_completeness(conn, chrono_id)
            alert = ""
            if ia_rate > 0.6 or unresolved_rate > 0.2 or completeness < 0.7:
                alert = "🔴"
            elif ia_rate > 0.4 or unresolved_rate > 0.1 or completeness < 0.9:
                alert = "⚠"
            records[log.name] = {
                "chrono_id": chrono_id,
                "auto_rate": auto_rate,
                "ia_rate": ia_rate,
                "unresolved_rate": unresolved_rate,
                "completeness": completeness,
                "alert": alert,
            }

    lines = [
        "| run log | id | auto | ia | non résolu | complétude | alerte |",
        "|---------|----|------|----|------------|------------|--------|",
    ]
    for name, data in records.items():
        lines.append(
            f"| {name} | {data['chrono_id']} | {_format_pct(data['auto_rate'])} | "
            f"{_format_pct(data['ia_rate'])} | {_format_pct(data['unresolved_rate'])} | "
            f"{_format_pct(data['completeness'])} | {data['alert']} |"
        )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_report()
