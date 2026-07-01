"""
components/result_section.py

Section 2 & 3 dari diskusi mockup:
- Tiga kartu hasil berdampingan (BFS | Dijkstra | A*)
- Tabel ranking semua blok per algoritma di bawahnya
"""

from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from core.constants import ALGORITHM_KEYS, ALGORITHM_LABELS, ALGORITHM_COLORS, MS_PER_SECOND
from components.result_card import build_result_card

# ID output yang diupdate oleh callback
RESULT_CARDS_ID  = "section-result-cards"
RESULT_TABLES_ID = "section-result-tables"

def build_result_cards_row(all_results: dict[str, Any] | None = None) -> dbc.Row:
    cards = []
    for key in ALGORITHM_KEYS:
        result = all_results.get(key) if all_results else None
        card = build_result_card(
            algorithm_key=key,
            algorithm_label=ALGORITHM_LABELS[key],
            result=result,
        )
        cards.append(dbc.Col(card, xs=12, md=4, className="mb-3"))

    return dbc.Row(cards, className="g-3")

def _build_ranking_table(algorithm_key: str, result: Any | None) -> dbc.Card:
    accent = ALGORITHM_COLORS[algorithm_key]
    label  = ALGORITHM_LABELS[algorithm_key]

    header = html.Div(
        f"Ranking — {label}",
        style={
            "backgroundColor": accent,
            "color": "#fff",
            "fontWeight": "600",
            "fontSize": "0.78rem",
            "padding": "5px 12px",
            "borderRadius": "6px 6px 0 0",
        },
    )

    if result is None or not result.all_reachable_blocks:
        body = dbc.CardBody(
            html.P("—", className="text-muted mb-0", style={"fontSize": "0.8rem"})
        )
        return dbc.Card([header, body], style={
            "background": "#1E293B", "border": f"1px solid {accent}", "borderRadius": "6px",
        })

    # Tentukan apakah BFS (pakai total_hops) atau Dijkstra/A* (pakai total_cost)
    sample = result.all_reachable_blocks[0]
    use_hops = hasattr(sample, "total_hops")
    metric_header = "Hop" if use_hops else "Cost"

    table_header = html.Thead(
        html.Tr([
            html.Th("#",       style={"width": "30px"}),
            html.Th("Blok"),
            html.Th(metric_header),
            html.Th("Jalur"),
        ]),
        style={"fontSize": "0.72rem", "color": "#64748B"},
    )

    rows = []
    for rank, info in enumerate(result.all_reachable_blocks, start=1):
        metric_value = info.total_hops if use_hops else info.total_cost
        path_str     = " → ".join(info.path_from_entrance)
        rows.append(
            html.Tr([
                html.Td(rank,         style={"color": "#64748B"}),
                html.Td(info.block_id, style={"color": accent, "fontWeight": "600"}),
                html.Td(metric_value,  style={"color": "#E2E8F0"}),
                html.Td(path_str,      style={"color": "#94A3B8", "fontSize": "0.7rem"}),
            ])
        )

    table = dbc.Table(
        [table_header, html.Tbody(rows)],
        bordered=False,
        hover=True,
        size="sm",
        style={"marginBottom": 0, "fontSize": "0.78rem"},
        className="table-dark",
    )

    body = dbc.CardBody(table, style={"padding": "8px"})

    return dbc.Card(
        [header, body],
        style={
            "background": "#1E293B",
            "border": f"1px solid {accent}",
            "borderRadius": "6px",
        },
    )

def build_result_tables_row(all_results: dict[str, Any] | None = None) -> dbc.Row:
    tables = []
    for key in ALGORITHM_KEYS:
        result = all_results.get(key) if all_results else None
        table  = _build_ranking_table(key, result)
        tables.append(dbc.Col(table, xs=12, md=4, className="mb-3"))

    return dbc.Row(tables, className="g-3")