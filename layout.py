"""
layout.py

Merakit semua komponen menjadi satu halaman Dash.
Tidak ada logika bisnis atau callback di sini — hanya struktur visual.

Struktur:
  Header (center)
  ├── Section 1: Input (kiri) | Graph Cytoscape + Tab (kanan)
  ├── Section 2: Kartu ringkasan hasil (3 kolom)
  └── Section 3: Tabel ranking lengkap (3 kolom)
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from core.models import ParkingCondition
from core.constants import ALGORITHM_KEYS

from components.input_panel import build_input_panel, build_algorithm_tabs, ALGO_TAB_ID
from components.graph_panel import (
    GRAPH_CYTO_ID, INTERVAL_ID, FRAME_STORE_ID, FRAME_INDEX_ID,
    build_cytoscape_graph, build_graph_legend,
)
from components.result_section import (
    RESULT_CARDS_ID, RESULT_TABLES_ID,
    build_result_cards_row, build_result_tables_row,
)
from callbacks.run_callback import ANIMATION_INTERVAL_MS, STEP_DESC_ID, STEP_INFO_ID

_BG     = "#0F172A"
_CARD   = "#1E293B"
_BORDER = "#334155"
_TEXT   = "#E2E8F0"
_MUTED  = "#64748B"

def _build_header() -> html.Div:
    return html.Div(
        html.Div([
            html.H4(
                "Smart Parking (Perbandingan 3 Algoritma Searching)",
                className="mb-1 fw-bold",
                style={"color": _TEXT, "letterSpacing": "0.01em"},
            ),
            html.P(
                "BFS  ·  Dijkstra  ·  A*",
                className="mb-0",
                style={"color": _MUTED, "fontSize": "0.85rem"},
            ),
        ], style={"textAlign": "center"}),
        style={
            "padding":      "20px 24px",
            "borderBottom": f"1px solid {_BORDER}",
            "background":   _CARD,
        },
    )

def _build_step_info_panel() -> html.Div:
    """Panel deskripsi langkah animasi yang aktif saat ini."""
    return html.Div([
        html.Div(
            id=STEP_DESC_ID,
            children="Pilih blok penuh, lalu klik Run All untuk memulai.",
            style={
                "fontSize":     "0.8rem",
                "color":        _TEXT,
                "padding":      "8px 12px",
                "background":   "#0F172A",
                "borderRadius": "6px",
                "marginBottom": "4px",
                "minHeight":    "36px",
            },
        ),
        html.Div(
            id=STEP_INFO_ID,
            style={"fontSize": "0.72rem", "color": _MUTED, "paddingLeft": "4px"},
        ),
    ], style={"marginBottom": "8px"})

def _build_graph_card() -> dbc.Card:
    """Card graph: tab algoritma + Cytoscape + panel langkah + legend."""
    default_condition = ParkingCondition(full_blocks=set())
    return dbc.Card(
        dbc.CardBody([
            build_algorithm_tabs(),
            html.Div(style={"marginTop": "6px"}),
            _build_step_info_panel(),
            build_cytoscape_graph(default_condition),
            html.Div(
                build_graph_legend(),
                style={
                    "display":    "flex",
                    "flexWrap":   "wrap",
                    "marginTop":  "8px",
                    "paddingLeft":"4px",
                },
            ),
        ]),
        style={"background": _CARD, "border": f"1px solid {_BORDER}", "height": "100%"},
        className="mb-3",
    )

def _section_header(title: str, subtitle: str) -> html.Div:
    return html.Div([
        html.H6(title, className="mb-0 fw-bold", style={"color": _TEXT}),
        html.P(subtitle, className="mb-0", style={"color": _MUTED, "fontSize": "0.78rem"}),
    ], className="mb-3", style={"borderLeft": "3px solid #6366F1", "paddingLeft": "10px"})

def build_layout() -> html.Div:
    return html.Div([
        _build_header(),

        dbc.Container([
            html.Div(className="mt-4"),

            # ── Section 1: Input + Graph ──────────────────────────────────
            dbc.Row([
                dbc.Col(
                    build_input_panel(),
                    xs=12, md=4,
                    style={"display": "flex", "flexDirection": "column"},
                ),
                dbc.Col(
                    _build_graph_card(),
                    xs=12, md=8,
                ),
            ], className="mb-4", style={"alignItems": "stretch"}),

            # ── Section 2: Kartu ringkasan ────────────────────────────────
            _section_header(
                "Hasil Terdekat",
                "Blok parkir paling dekat dari ENTRANCE per algoritma",
            ),
            html.Div(
                build_result_cards_row(all_results=None),
                id=RESULT_CARDS_ID,
                className="mb-4",
            ),

            # ── Section 3: Tabel ranking ──────────────────────────────────
            _section_header(
                "Ranking Semua Blok",
                "Urutan seluruh blok berdasarkan cost / hop dari ENTRANCE",
            ),
            html.Div(
                build_result_tables_row(all_results=None),
                id=RESULT_TABLES_ID,
                className="mb-5",
            ),
        ], fluid=True, style={"maxWidth": "1200px"}),

        # ── Hidden state components ───────────────────────────────────────
        dcc.Interval(
            id=INTERVAL_ID,
            interval=ANIMATION_INTERVAL_MS,
            disabled=True,
            n_intervals=0,
        ),
        dcc.Store(id=FRAME_STORE_ID, storage_type="memory"),
        dcc.Store(id=FRAME_INDEX_ID, storage_type="memory"),

    ], style={"background": _BG, "minHeight": "100vh", "fontFamily": "'Inter', sans-serif"})