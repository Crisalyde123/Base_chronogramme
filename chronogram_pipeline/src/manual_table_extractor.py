"""Minimal example implementing header and data range detection.

This script demonstrates the logic described in the specification
for tasks C.1.2, C.2, C.2.1 and C.2.2 using plain Python lists.
"""

from __future__ import annotations

from typing import List, Tuple


KNOWN_HEADERS = [
    "Heure",
    "Descriptif",
    "Émetteur",
    "Cellule concernée",
    "Canal",
    "Phasage",
    "Nom de l’inject",
]

STANDARD_FIELDS = [
    "Horodatage",
    "Contenu",
    "Emetteur",
    "Destinataire",
    "Modalité",
    "Phase",
    "ID_inject",
]


def _norm(text: str | None) -> str:
    """Return ``text`` lowercased and stripped, or an empty string if ``None``."""
    return "" if text is None else str(text).strip().lower()


def detect_header_row(lines: List[List[str]]) -> int:
    """Return index of the header row based on known header names."""
    for idx, row in enumerate(lines):
        matches = sum(_norm(cell) in { _norm(h) for h in KNOWN_HEADERS } for cell in row)
        if matches >= 2:
            return idx
    return 0


def detect_last_data_row(lines: List[List[str]], header_idx: int) -> int:
    """Return index of the last non-empty row after header_idx."""
    empty_streak = 0
    last = header_idx
    for idx in range(header_idx + 1, len(lines)):
        if all(_norm(c) == "" for c in lines[idx]):
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0
            last = idx
    return last


def map_headers(headers: List[str]) -> List[Tuple[str, str]]:
    """Map raw headers to standard fields or ``Inconnu``."""
    mapping = []
    rules = { _norm(k): v for k, v in zip(KNOWN_HEADERS, STANDARD_FIELDS) }
    for h in headers:
        std = rules.get(_norm(h), "Inconnu")
        mapping.append((h, std))
    return mapping


if __name__ == "__main__":
    sample_lines = [
        ["Fiche exercice : XY", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["Phase", "", "", "", "", ""],
        ["Heure", "Descriptif", "Émetteur", "Cellule concernée", "Canal", ""],
        ["T0", "Message initial", "Préfecture", "PC", "Email", ""],
        ["T0+5", "Message 2", "SDIS", "Direction", "Téléphone", ""],
        ["", "", "", "", "", ""],
        ["", "", "", "", "", ""],
    ]

    header_idx = detect_header_row(sample_lines)
    last_idx = detect_last_data_row(sample_lines, header_idx)
    headers = sample_lines[header_idx]
    mappings = map_headers(headers)

    print(f"Ligne d'en-tête détectée : Ligne {header_idx + 1}")
    print(f"Dernière ligne utile : Ligne {last_idx + 1}")
    print(f"Plage extraite : lignes {header_idx + 1} à {last_idx + 1}")
    print("Colonnes extraites : ", ", ".join(headers))
    print("Mapping en-têtes proposé :")
    for orig, std in mappings:
        print(f"  - '{orig}' -> '{std}'")
