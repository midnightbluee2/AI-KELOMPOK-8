"""
components/graph_panel.py

Komponen visualisasi graf parkir menggunakan Dash Cytoscape.

Cytoscape dipilih karena dirancang khusus untuk graf node-edge:
- Update animasi cukup kirim list `elements` baru, tidak perlu rebuild figure
- Warna node dikontrol via CSS class, mudah diganti per status
- Blok penuh tetap tampil sebagai node (class "full"), tanpa edge ke lantai

Warna node (lihat NODE_COLORS di core/constants.py):
    entrance → ungu        floor   → abu
    available→ hijau       full    → hitam (node ada, tanpa edge)
    visited  → biru muda   current → biru terang (node aktif)
    path     → oranye      target  → hijau terang (blok tujuan)
"""

from __future__ import annotations
from typing import Any

import dash_cytoscape as cyto
from dash import html
import dash_bootstrap_components as dbc

from core.constants import (
    ENTRANCE_NODE, FLOOR_NODES, PARKING_BLOCKS,
    ALGORITHM_COLORS, NODE_COLORS,
)
from core.models import ParkingCondition, build_parking_graph
from core.animator import AlgorithmStep

# Dash component IDs
GRAPH_CYTO_ID  = "cyto-graph"
ALGO_TAB_ID    = "tab-algorithm"
INTERVAL_ID    = "interval-animation"
FRAME_STORE_ID = "store-frames"
FRAME_INDEX_ID = "store-frame-index"

_FLOOR_X: dict[str, float] = {
    "A": 150,
    "B": 450,
    "C": 750,
    "D": 1050,
}

# 5 blok tersebar di rentang ±100px dari pusat lantai, jarak antar blok 50px
_BLOCK_OFFSETS: list[float] = [-100, -50, 0, 50, 100]

_NODE_POSITIONS: dict[str, dict[str, float]] = {
    "ENTRANCE": {"x": 600, "y": 50},
    **{
        floor: {"x": _FLOOR_X[floor], "y": 200}
        for floor in ("A", "B", "C", "D")
    },
    **{
        f"{floor}{i + 1}": {"x": _FLOOR_X[floor] + _BLOCK_OFFSETS[i], "y": 380}
        for floor in ("A", "B", "C", "D")
        for i in range(5)
    },
}

# Stylesheet Cytoscape — setiap class node punya warna sendiri
CYTOSCAPE_STYLESHEET: list[dict] = [
    {
        "selector": "node",
        "style": {
            "label":        "data(label)",
            "text-valign":  "center",
            "text-halign":  "center",
            "color":        "#FFFFFF",
            "font-size":    "10px",
            "font-weight":  "bold",
            "font-family":  "monospace",
            "width":        "40px",
            "height":       "40px",
            "border-width": "2px",
            "border-color": "#0F172A",
        },
    },
    {"selector": ".entrance",  "style": {"background-color": NODE_COLORS["entrance"]}},
    {"selector": ".floor",     "style": {"background-color": NODE_COLORS["floor"]}},
    {"selector": ".available", "style": {"background-color": NODE_COLORS["available"]}},
    {"selector": ".full",      "style": {
        "background-color": NODE_COLORS["full"],
        "border-color":     "#334155",
        "border-width":     "1px",
    }},
    {"selector": ".visited",   "style": {"background-color": NODE_COLORS["visited"]}},
    {"selector": ".current",   "style": {
        "background-color": NODE_COLORS["current"],
        "border-color":     "#FFFFFF",
        "border-width":     "3px",
        "width":            "48px",
        "height":           "48px",
    }},
    {"selector": ".path",      "style": {"background-color": NODE_COLORS["path"]}},
    {"selector": ".target",    "style": {"background-color": NODE_COLORS["target"]}},
    {
        "selector": "edge",
        "style": {
            "label":                   "data(weight)",
            "font-size":               "9px",
            "line-color":              "#475569",
            "width":                   "2px",
            "curve-style":             "bezier",
            "text-background-color":   "#0F172A",
            "text-background-opacity": 0.8,
            "text-background-padding": "2px",
            "color":                   "#94A3B8",
        },
    },
]

# Helpers

def _resolve_node_class(
    node_id:    str,
    condition:  ParkingCondition,
    step:       AlgorithmStep | None,
    final_path: list[str],
    is_final:   bool,
) -> str:
    if step and node_id == step.current_node:
        return "current"
    if is_final and final_path and node_id == final_path[-1]:
        return "target"
    if is_final and node_id in set(final_path):
        return "path"
    if step and node_id in step.visited_nodes:
        return "visited"
    if not condition.is_block_available(node_id) and node_id not in FLOOR_NODES and node_id != ENTRANCE_NODE:
        return "full"
    if node_id == ENTRANCE_NODE:
        return "entrance"
    if node_id in FLOOR_NODES:
        return "floor"
    return "available"

def build_cytoscape_elements(
    condition:  ParkingCondition,
    step:       AlgorithmStep | None = None,
    final_path: list[str]            = (),
    is_final:   bool                 = False,
) -> list[dict]:
    logic_graph  = build_parking_graph(condition.get_available_block_ids())
    full_path    = list(final_path)
    elements:  list[dict] = []
    added_ids: set[str]   = set()

    # Node dari graf logika (ENTRANCE + lantai + blok tersedia)
    for node_id in logic_graph.nodes():
        css_class = _resolve_node_class(node_id, condition, step, full_path, is_final)
        elements.append({
            "data":     {"id": node_id, "label": node_id},
            "classes":  css_class,
            "position": _NODE_POSITIONS.get(node_id, {"x": 0, "y": 0}),
        })
        added_ids.add(node_id)

    # Node blok penuh — tidak ada di graf logika, ditambahkan manual
    for floor_id, blocks in PARKING_BLOCKS.items():
        for block_id in blocks:
            if block_id not in added_ids:
                elements.append({
                    "data":     {"id": block_id, "label": block_id},
                    "classes":  "full",
                    "position": _NODE_POSITIONS.get(block_id, {"x": 0, "y": 0}),
                })

    # Edge — hanya untuk blok yang tersedia
    for node_a, node_b, data in logic_graph.edges(data=True):
        elements.append({
            "data": {
                "source": node_a,
                "target": node_b,
                "weight": str(data["weight"]),
            }
        })

    return elements

# Komponen 

def build_cytoscape_graph(condition: ParkingCondition) -> html.Div:
    """
    Dibungkus dalam Div dengan tinggi & overflow tetap, supaya:
    - Cytoscape selalu tahu ukuran container-nya sejak render pertama
      (menghindari bug "fit" salah hitung karena container masih 0px saat mount)
    - Saat user pan/zoom, konten tidak pernah bocor keluar dari card
    """
    return html.Div(
        cyto.Cytoscape(
            id=GRAPH_CYTO_ID,
            elements=build_cytoscape_elements(condition),
            stylesheet=CYTOSCAPE_STYLESHEET,
            layout={
                "name":    "preset",
                "fit":     True,   # otomatis zoom & pan agar semua node terlihat
                "padding": 50,     # jarak aman dari tepi supaya node tidak terpotong
            },
            style={"width": "100%", "height": "100%"},
            responsive=True,          # auto re-fit saat ukuran container berubah
            minZoom=0.4,               # batas zoom-out
            maxZoom=2.5,                # batas zoom-in, agar tidak "hilang" saat zoom
            wheelSensitivity=0.25,       # scroll zoom lebih halus, tidak lompat jauh
            userPanningEnabled=True,
            userZoomingEnabled=True,
            autoungrabify=True,          # node tidak bisa digeser tidak sengaja
        ),
        style={
            "width":        "100%",
            "height":       "520px",
            "overflow":     "hidden",
            "borderRadius": "8px",
            "border":       "1px solid #334155",
            "background":   "#0F172A",
        },
    )

def build_graph_legend() -> list:
    items = [
        (NODE_COLORS["entrance"],  "ENTRANCE"),
        (NODE_COLORS["floor"],     "Lantai"),
        (NODE_COLORS["available"], "Tersedia"),
        (NODE_COLORS["full"],      "Penuh"),
        (NODE_COLORS["visited"],   "Dikunjungi"),
        (NODE_COLORS["current"],   "Sedang diproses"),
        (NODE_COLORS["path"],      "Jalur terpilih"),
        (NODE_COLORS["target"],    "Blok tujuan"),
    ]
    return [
        html.Span([
            html.Span(style={
                "display":         "inline-block",
                "width":           "10px",
                "height":          "10px",
                "borderRadius":    "50%",
                "backgroundColor": color,
                "marginRight":     "4px",
                "border":          "1px solid #334155",
            }),
            html.Span(label, style={"fontSize": "0.75rem", "color": "#94A3B8"}),
        ], style={"marginRight": "12px", "whiteSpace": "nowrap"})
        for color, label in items
    ]
