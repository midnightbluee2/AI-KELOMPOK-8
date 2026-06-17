"""
gui_dash/app.py — Visualisasi Dijkstra untuk sistem parkir menggunakan Dash + Cytoscape.

Cara menjalankan:
    cd src
    python gui-dash/app.py
    Buka browser: http://localhost:8050
"""

import sys
import os

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_cytoscape as cyto

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from algorithms import (
    ENTRANCE_NODE,
    FLOOR_NODES,
    PARKING_BLOCKS,
    NODE_COLORS,
    ParkingCondition,
    SearchResult,
    AlgorithmStep,
    build_parking_graph,
    run_dijkstra,
)

# --- Konstanta UI ---

APP_TITLE          = "Dijkstra — Parking Lot Finder"
AUTO_PLAY_INTERVAL = 800  # milidetik antar langkah saat auto-play
CYTOSCAPE_HEIGHT   = "560px"

# Posisi node di canvas Cytoscape (piksel)
NODE_POSITIONS_PX: dict[str, dict[str, float]] = {
    "ENTRANCE": {"x": 80,  "y": 300},
    "A": {"x": 260, "y": 80},  "B": {"x": 260, "y": 200},
    "C": {"x": 260, "y": 340}, "D": {"x": 260, "y": 460},
    "A1": {"x": 480, "y": 20},  "A2": {"x": 480, "y": 60},
    "A3": {"x": 480, "y": 100}, "A4": {"x": 480, "y": 140}, "A5": {"x": 480, "y": 180},
    "B1": {"x": 480, "y": 220}, "B2": {"x": 480, "y": 260},
    "B3": {"x": 480, "y": 300}, "B4": {"x": 480, "y": 340}, "B5": {"x": 480, "y": 380},
    "C1": {"x": 480, "y": 420}, "C2": {"x": 480, "y": 460},
    "C3": {"x": 480, "y": 500}, "C4": {"x": 480, "y": 540}, "C5": {"x": 480, "y": 580},
    "D1": {"x": 480, "y": 620}, "D2": {"x": 480, "y": 660},
    "D3": {"x": 480, "y": 700}, "D4": {"x": 480, "y": 740}, "D5": {"x": 480, "y": 780},
}

# Stylesheet Cytoscape: aturan visual tiap kelas node
CYTOSCAPE_STYLESHEET: list[dict] = [
    {
        "selector": "node",
        "style": {
            "label":        "data(label)",
            "text-valign":  "center",
            "text-halign":  "center",
            "color":        "#FFFFFF",
            "font-size":    "11px",
            "font-weight":  "bold",
            "width":        "44px",
            "height":       "44px",
            "border-width": "2px",
            "border-color": "#FFFFFF",
        },
    },
    {"selector": ".entrance",  "style": {"background-color": NODE_COLORS["entrance"]}},
    {"selector": ".floor",     "style": {"background-color": NODE_COLORS["floor"]}},
    {"selector": ".available", "style": {"background-color": NODE_COLORS["available"]}},
    {"selector": ".full",      "style": {"background-color": NODE_COLORS["full"]}},
    {"selector": ".visited",   "style": {"background-color": NODE_COLORS["visited"]}},
    {"selector": ".current",   "style": {
        "background-color": NODE_COLORS["visited"],
        "border-color":     "#FFFFFF",
        "border-width":     "4px",
        "width":            "54px",
        "height":           "54px",
    }},
    {"selector": ".path",   "style": {"background-color": NODE_COLORS["path"]}},
    {"selector": ".target", "style": {"background-color": NODE_COLORS["target"]}},
    {
        "selector": "edge",
        "style": {
            "label":                     "data(weight)",
            "font-size":                 "9px",
            "line-color":                "#AAAAAA",
            "width":                     "2px",
            "curve-style":               "bezier",
            "text-background-color":     "#FFFFFF",
            "text-background-opacity":   0.7,
            "text-background-padding":   "2px",
        },
    },
]


# --- Builder elemen Cytoscape ---

def build_cytoscape_elements(
    full_blocks: list[str],
    result: SearchResult | None,
    step_index: int,
) -> list[dict]:
    """Bangun daftar node + edge untuk Cytoscape berdasarkan kondisi dan langkah animasi."""
    full_blocks_set = set(full_blocks)
    condition       = ParkingCondition(full_blocks=full_blocks_set)
    graph           = build_parking_graph(condition.get_available_block_ids())

    current_step: AlgorithmStep | None = None
    if result and result.all_steps:
        current_step = result.all_steps[min(step_index, len(result.all_steps) - 1)]

    elements: list[dict] = []

    for node_id in graph.nodes():
        css_class = _resolve_node_css_class(node_id, full_blocks_set, result, current_step)
        elements.append({
            "data":     {"id": node_id, "label": node_id},
            "classes":  css_class,
            "position": NODE_POSITIONS_PX.get(node_id, {"x": 0, "y": 0}),
        })

    # Blok penuh tidak ada di graph, tapi tetap ditampilkan
    for block_id in full_blocks_set:
        if block_id not in [el["data"]["id"] for el in elements]:
            elements.append({
                "data":     {"id": block_id, "label": block_id},
                "classes":  "full",
                "position": NODE_POSITIONS_PX.get(block_id, {"x": 0, "y": 0}),
            })

    for node_a, node_b, data in graph.edges(data=True):
        elements.append({"data": {"source": node_a, "target": node_b, "weight": str(data["weight"])}})

    return elements


def _resolve_node_css_class(
    node_id: str,
    full_blocks: set[str],
    result: SearchResult | None,
    step: AlgorithmStep | None,
) -> str:
    """
    Tentukan kelas CSS Cytoscape untuk satu node.
    Prioritas: current > target > path > visited > full > entrance > floor > available.
    """
    if step and node_id == step.current_node:
        return "current"
    if result and result.is_found and node_id == result.nearest_block_id:
        return "target"
    if result and result.is_found and node_id in result.nearest_block_path:
        return "path"
    if step and node_id in step.visited_nodes:
        return "visited"
    if node_id in full_blocks:
        return "full"
    if node_id == ENTRANCE_NODE:
        return "entrance"
    if node_id in FLOOR_NODES:
        return "floor"
    return "available"


# --- Builder komponen UI ---

def build_block_toggles() -> list[html.Div]:
    """Bangun checkbox toggle per lantai untuk menandai blok yang penuh."""
    toggle_sections: list[html.Div] = []

    for floor_id in FLOOR_NODES:
        block_options = [{"label": b, "value": b} for b in PARKING_BLOCKS[floor_id]]
        toggle_sections.append(html.Div([
            html.P(f"Lantai {floor_id}", style={"fontWeight": "bold", "marginBottom": "4px"}),
            dcc.Checklist(
                id=f"checklist-floor-{floor_id}",
                options=block_options,
                value=[],
                style={"display": "flex", "flexWrap": "wrap", "gap": "6px"},
                labelStyle={"fontSize": "13px"},
            ),
        ], style={"marginBottom": "12px"}))

    return toggle_sections


def build_metrics_display(result: SearchResult | None) -> html.Div:
    """Bangun panel metrik hasil pencarian Dijkstra."""
    if result is None:
        return html.Div("Belum ada hasil pencarian.", style={"color": "#888"})

    metrics = [
        ("Algoritma",       result.algorithm_name),
        ("Blok Terdekat",   result.nearest_block_id or "Tidak ada"),
        ("Total Cost",      f"{result.nearest_block_cost:.1f}" if result.is_found else "-"),
        ("Node Dikunjungi", str(result.total_visited)),
        ("Waktu Pencarian", f"{result.elapsed_ms:.4f} ms"),
        ("Jalur",           result.path_display),
    ]

    metric_cards = [
        html.Div([
            html.P(label, style={"fontSize": "11px", "color": "#888", "marginBottom": "2px"}),
            html.P(value, style={"fontSize": "15px", "fontWeight": "bold", "margin": "0"}),
        ], style={"background": "#1E1E2E", "borderRadius": "8px", "padding": "10px 14px", "minWidth": "120px"})
        for label, value in metrics
    ]

    return html.Div(metric_cards, style={"display": "flex", "flexWrap": "wrap", "gap": "10px"})


# --- Layout ---

def create_app_layout() -> html.Div:
    """Buat layout utama: panel kiri (kontrol) + panel kanan (graf Cytoscape)."""
    return html.Div([
        dcc.Store(id="store-result",     data=None),
        dcc.Store(id="store-step",       data=0),
        dcc.Store(id="store-is-playing", data=False),
        dcc.Interval(id="interval-autoplay", interval=AUTO_PLAY_INTERVAL, disabled=True),

        # Header
        html.Div([
            html.H2("🅿️ Parking Lot Finder — Dijkstra", style={"margin": "0"}),
            html.P(
                "Dijkstra mencari blok terdekat berdasarkan total bobot edge (cost). "
                "Node dengan cost terkecil selalu diproses lebih dulu via priority queue.",
                style={"color": "#AAA", "margin": "4px 0 0 0", "fontSize": "13px"},
            ),
        ], style={"padding": "16px 24px", "borderBottom": "1px solid #333"}),

        # Body
        html.Div([

            # Panel kiri
            html.Div([
                html.H4("🅿️ Kondisi Parkir", style={"marginBottom": "12px"}),
                html.P("Centang blok yang penuh:", style={"fontSize": "12px", "color": "#AAA"}),
                *build_block_toggles(),

                html.Hr(style={"borderColor": "#444"}),
                html.Button("🔍 Jalankan Dijkstra", id="btn-run", style={
                    "width": "100%", "padding": "10px", "background": "#4A90D9",
                    "color": "white", "border": "none", "borderRadius": "8px",
                    "cursor": "pointer", "fontWeight": "bold", "marginBottom": "16px",
                }),

                html.Hr(style={"borderColor": "#444"}),
                html.H4("⏱ Kontrol Animasi", style={"marginBottom": "8px"}),
                html.Div([
                    html.Button("⏮",  id="btn-reset", title="Reset",     style=_btn_style()),
                    html.Button("◀",  id="btn-prev",  title="Prev Step", style=_btn_style()),
                    html.Button("▶",  id="btn-next",  title="Next Step", style=_btn_style()),
                    html.Button("▶▶", id="btn-auto",  title="Auto Play", style=_btn_style("#4A90D9")),
                ], style={"display": "flex", "gap": "8px", "marginBottom": "12px"}),
                html.Div(id="display-step-info", style={"fontSize": "12px", "color": "#AAA"}),

                html.Hr(style={"borderColor": "#444"}),
                html.H4("📊 Metrik", style={"marginBottom": "8px"}),
                html.Div(id="display-metrics"),

                html.Hr(style={"borderColor": "#444"}),
                _build_legend(),

            ], style={
                "width": "300px", "minWidth": "300px", "padding": "16px",
                "background": "#161622", "overflowY": "auto",
                "height": "calc(100vh - 80px)",
            }),

            # Panel kanan: graf
            html.Div([
                html.Div(id="display-step-description", style={
                    "padding": "10px 16px", "background": "#1E1E2E",
                    "borderRadius": "8px", "marginBottom": "12px",
                    "fontSize": "13px", "color": "#DDD", "minHeight": "40px",
                }),
                cyto.Cytoscape(
                    id="cyto-graph",
                    elements=build_cytoscape_elements([], None, 0),
                    stylesheet=CYTOSCAPE_STYLESHEET,
                    layout={"name": "preset"},
                    style={"width": "100%", "height": CYTOSCAPE_HEIGHT},
                ),
            ], style={"flex": "1", "padding": "16px", "overflowY": "auto"}),

        ], style={"display": "flex", "height": "calc(100vh - 80px)"}),

    ], style={"fontFamily": "Inter, sans-serif", "background": "#0F0F1A", "color": "#FFFFFF", "minHeight": "100vh"})


def _btn_style(bg_color: str = "#2A2A3E") -> dict:
    """Style tombol kontrol animasi."""
    return {
        "padding": "8px 14px", "background": bg_color, "color": "white",
        "border": "none", "borderRadius": "6px", "cursor": "pointer", "fontWeight": "bold",
    }


def _build_legend() -> html.Div:
    """Bangun legenda warna node di panel kiri."""
    legend_items = [
        (NODE_COLORS["entrance"],  "ENTRANCE"),
        (NODE_COLORS["floor"],     "Lantai"),
        (NODE_COLORS["available"], "Tersedia"),
        (NODE_COLORS["full"],      "Penuh"),
        (NODE_COLORS["visited"],   "Dikunjungi"),
        (NODE_COLORS["path"],      "Jalur"),
        (NODE_COLORS["target"],    "Tujuan"),
    ]
    items = [
        html.Div([
            html.Span(style={
                "display": "inline-block", "width": "14px", "height": "14px",
                "borderRadius": "50%", "background": color,
                "marginRight": "8px", "verticalAlign": "middle",
            }),
            html.Span(label, style={"fontSize": "12px"}),
        ], style={"marginBottom": "4px"})
        for color, label in legend_items
    ]
    return html.Div([html.H4("🎨 Legenda", style={"marginBottom": "8px"}), *items])


# --- Inisialisasi app ---

app = dash.Dash(__name__, title=APP_TITLE)
app.layout = create_app_layout()


# --- Callbacks ---

def _get_all_full_blocks(*checklists: list[str]) -> list[str]:
    """Gabungkan semua blok yang dipilih dari semua checklist lantai."""
    full_blocks: list[str] = []
    for checklist in checklists:
        full_blocks.extend(checklist or [])
    return full_blocks


@app.callback(
    Output("store-result", "data"),
    Output("store-step",   "data"),
    Input("btn-run", "n_clicks"),
    State("checklist-floor-A", "value"),
    State("checklist-floor-B", "value"),
    State("checklist-floor-C", "value"),
    State("checklist-floor-D", "value"),
    prevent_initial_call=True,
)
def callback_run_dijkstra(
    _n_clicks: int,
    floor_a: list[str], floor_b: list[str],
    floor_c: list[str], floor_d: list[str],
) -> tuple[dict, int]:
    """Jalankan Dijkstra saat tombol diklik; simpan hasil ke dcc.Store."""
    full_blocks = _get_all_full_blocks(floor_a, floor_b, floor_c, floor_d)
    condition   = ParkingCondition(full_blocks=set(full_blocks))
    graph       = build_parking_graph(condition.get_available_block_ids())
    result      = run_dijkstra(graph)

    result_dict = {
        "nearest_block_id":   result.nearest_block_id,
        "nearest_block_path": result.nearest_block_path,
        "nearest_block_cost": result.nearest_block_cost,
        "total_visited":      result.total_visited,
        "elapsed_ms":         result.elapsed_ms,
        "path_display":       result.path_display,
        "algorithm_name":     result.algorithm_name,
        "is_found":           result.is_found,
        "total_steps":        len(result.all_steps),
        "steps": [
            {
                "visited_nodes": list(s.visited_nodes),
                "current_node":  s.current_node,
                "current_path":  s.current_path,
                "description":   s.description,
            }
            for s in result.all_steps
        ],
    }
    return result_dict, 0


@app.callback(
    Output("store-step",        "data", allow_duplicate=True),
    Output("store-is-playing",  "data"),
    Output("interval-autoplay", "disabled"),
    Input("btn-reset", "n_clicks"),
    Input("btn-prev",  "n_clicks"),
    Input("btn-next",  "n_clicks"),
    Input("btn-auto",  "n_clicks"),
    Input("interval-autoplay", "n_intervals"),
    State("store-step",       "data"),
    State("store-result",     "data"),
    State("store-is-playing", "data"),
    prevent_initial_call=True,
)
def callback_control_animation(
    _reset, _prev, _next, _auto, _interval,
    current_step: int,
    result_data: dict | None,
    is_playing: bool,
) -> tuple[int, bool, bool]:
    """Tangani navigasi langkah: Reset, Prev, Next, Auto-play, dan tick interval."""
    if result_data is None:
        return 0, False, True

    triggered_id = callback_context.triggered_id
    total_steps  = result_data.get("total_steps", 1)

    if triggered_id == "btn-reset":
        return 0, False, True
    if triggered_id == "btn-prev":
        return max(0, current_step - 1), False, True
    if triggered_id == "btn-next":
        return min(total_steps - 1, current_step + 1), False, True
    if triggered_id == "btn-auto":
        new_playing = not is_playing
        return current_step, new_playing, not new_playing
    if triggered_id == "interval-autoplay":
        next_step = current_step + 1
        if next_step >= total_steps:
            return total_steps - 1, False, True
        return next_step, True, False

    return current_step, is_playing, not is_playing


@app.callback(
    Output("cyto-graph",               "elements"),
    Output("display-metrics",          "children"),
    Output("display-step-description", "children"),
    Output("display-step-info",        "children"),
    Input("store-result", "data"),
    Input("store-step",   "data"),
    State("checklist-floor-A", "value"),
    State("checklist-floor-B", "value"),
    State("checklist-floor-C", "value"),
    State("checklist-floor-D", "value"),
)
def callback_update_display(
    result_data: dict | None,
    step_index: int,
    floor_a: list[str], floor_b: list[str],
    floor_c: list[str], floor_d: list[str],
) -> tuple:
    """Perbarui tampilan graf, metrik, dan deskripsi langkah setiap kali state berubah."""
    full_blocks = _get_all_full_blocks(floor_a, floor_b, floor_c, floor_d)

    if result_data is None:
        elements = build_cytoscape_elements(full_blocks, None, 0)
        return elements, build_metrics_display(None), "Jalankan Dijkstra untuk melihat animasi.", ""

    result   = _deserialize_result(result_data)
    elements = build_cytoscape_elements(full_blocks, result, step_index)
    metrics  = build_metrics_display(result)

    safe_index  = min(step_index, len(result.all_steps) - 1)
    step        = result.all_steps[safe_index]
    step_info   = f"Langkah {safe_index + 1} dari {len(result.all_steps)}"

    return elements, metrics, step.description, step_info


def _deserialize_result(result_data: dict) -> SearchResult:
    """Konversi dict dari dcc.Store kembali ke objek SearchResult."""
    steps = [
        AlgorithmStep(
            visited_nodes=set(s["visited_nodes"]),
            current_node=s["current_node"],
            current_path=s["current_path"],
            description=s["description"],
        )
        for s in result_data.get("steps", [])
    ]
    return SearchResult(
        nearest_block_id   = result_data["nearest_block_id"],
        nearest_block_path = result_data["nearest_block_path"],
        nearest_block_cost = result_data["nearest_block_cost"],
        all_visited_nodes  = set(),
        all_steps          = steps,
        elapsed_ms         = result_data["elapsed_ms"],
        algorithm_name     = result_data["algorithm_name"],
    )


# --- Entry point ---

if __name__ == "__main__":
    app.run(debug=True)