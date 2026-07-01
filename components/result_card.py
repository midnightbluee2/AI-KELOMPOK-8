"""
components/result_card.py

Satu kartu hasil untuk satu algoritma.
Menampilkan: blok terdekat, cost/hop, jalur, waktu pencarian.
Bisa dalam state kosong (belum dijalankan) atau berisi hasil.
"""

from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from core.constants import ALGORITHM_COLORS, MS_PER_SECOND

def _format_elapsed(elapsed_seconds: float) -> str:
    return f"{elapsed_seconds * MS_PER_SECOND:.4f} ms"

def _format_path(path: list[str]) -> str:
    return " → ".join(path)

def _cost_label(nearest: Any) -> tuple[str, str]:
    if hasattr(nearest, "total_hops"):
        return "Jumlah Hop", str(nearest.total_hops)
    return "Total Cost", str(nearest.total_cost)

def build_result_card(algorithm_key: str, algorithm_label: str, result: Any | None = None) -> dbc.Card:
    accent_color = ALGORITHM_COLORS[algorithm_key]

    header = html.Div(
        algorithm_label,
        style={
            "backgroundColor": accent_color,
            "color": "#fff",
            "fontWeight": "700",
            "fontSize": "0.85rem",
            "letterSpacing": "0.08em",
            "padding": "6px 14px",
            "borderRadius": "6px 6px 0 0",
        },
    )

    if result is None or not result.is_found:
        body = dbc.CardBody(
            html.P(
                "Belum dijalankan" if result is None else "Tidak ada blok tersedia.",
                className="text-muted mb-0",
                style={"fontSize": "0.8rem"},
            )
        )
    else:
        nearest = result.nearest_block
        metric_name, metric_value = _cost_label(nearest)

        rows = [
            ("Blok terdekat",  nearest.block_id),
            (metric_name,      metric_value),
            ("Jalur",          _format_path(nearest.path_from_entrance)),
            ("Waktu",          _format_elapsed(result.elapsed_seconds)),
        ]

        body = dbc.CardBody(
            [
                html.Div(
                    [
                        html.Span(label, style={"color": "#64748B", "fontSize": "0.7rem", "display": "block"}),
                        html.Span(value, style={"color": "#E2E8F0", "fontSize": "0.82rem", "wordBreak": "break-word"}),
                    ],
                    className="mb-2",
                )
                for label, value in rows
            ]
        )

    return dbc.Card(
        [header, body],
        style={
            "background": "#1E293B",
            "border": f"1px solid {accent_color}",
            "borderRadius": "6px",
            "height": "100%",
        },
    )