"""
components/input_panel.py

Komponen input: checklist blok parkir per lantai + tombol Run All.
Tidak ada logika bisnis — hanya layout UI.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from core.constants import FLOOR_NODES, PARKING_BLOCKS, ALGORITHM_COLORS

# ID elemen (dipusat agar tidak ada string literal tersebar)
INPUT_CHECKLIST_ID = "input-full-blocks"
RUN_BUTTON_ID      = "btn-run-all"
ALGO_TAB_ID        = "tab-algorithm"   # re-export agar layout bisa import dari sini

def _build_floor_column(floor_id: str) -> dbc.Col:
    """Satu kolom checklist untuk satu lantai."""
    options = [{"label": b, "value": b} for b in PARKING_BLOCKS[floor_id]]
    return dbc.Col([
        html.P(
            f"Lantai {floor_id}",
            className="fw-semibold mb-1",
            style={"color": "#CBD5E1", "fontSize": "0.8rem", "letterSpacing": "0.05em"},
        ),
        dcc.Checklist(
            id={"type": INPUT_CHECKLIST_ID, "floor": floor_id},
            options=options,
            value=[],
            labelStyle={"display": "block", "marginBottom": "4px", "fontSize": "0.85rem", "color": "#E2E8F0"},
            inputStyle={"marginRight": "6px", "accentColor": "#F87171"},
        ),
    ], xs=6, sm=3)

def build_algorithm_tabs() -> dbc.Tabs:
    tab_items = [
        dbc.Tab(
            label=label,
            tab_id=key,
            label_style={"color": ALGORITHM_COLORS[key], "fontWeight": "600"},
            active_label_style={"backgroundColor": ALGORITHM_COLORS[key], "color": "#fff"},
        )
        for key, label in [("bfs", "BFS"), ("dijkstra", "Dijkstra"), ("astar", "A*")]
    ]
    return dbc.Tabs(
        tab_items,
        id=ALGO_TAB_ID,
        active_tab="bfs",
        className="mb-0",
        style={"borderBottom": "none"},
    )

def build_input_panel() -> dbc.Card:
    floor_checklists = dbc.Row(
        [_build_floor_column(f) for f in FLOOR_NODES],
        className="g-3",
    )

    run_button = dbc.Button(
        [html.I(className="bi bi-play-fill me-2"), "Run All"],
        id=RUN_BUTTON_ID,
        color="primary",
        size="lg",
        className="w-100 mt-3",
        style={"background": "linear-gradient(135deg, #6366F1, #3B82F6)", "border": "none"},
    )

    return dbc.Card(
        dbc.CardBody([
            html.H6(
                "Pilih Blok yang Penuh",
                className="text-uppercase fw-bold mb-3",
                style={"color": "#94A3B8", "fontSize": "0.75rem", "letterSpacing": "0.1em"},
            ),
            floor_checklists,
            run_button,
        ]),
        style={"background": "#1E293B", "border": "1px solid #334155"},
    )
