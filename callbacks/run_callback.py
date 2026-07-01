"""
callbacks/run_callback.py

Tiga callback utama aplikasi Smart Parking:

1. on_run_all()
   Trigger: tombol Run All
   - Jalankan ketiga algoritma via runner.run_all()
   - Serialisasi TraceResult + SearchResult ke dcc.Store
   - Reset frame index semua algoritma ke 0
   - Aktifkan dcc.Interval untuk mulai animasi
   - Update kartu hasil & tabel ranking

2. on_animation_tick()
   Trigger: dcc.Interval setiap ANIMATION_INTERVAL_MS
   - Baca step index tab aktif dari store
   - Render Cytoscape elements sesuai AlgorithmStep pada index tersebut
   - Increment index; matikan interval kalau animasi selesai
   - Update panel deskripsi langkah

3. on_tab_switch()
   Trigger: user klik tab algoritma
   - Jika tab sudah selesai → tampilkan frame terakhir (path highlight)
   - Jika tab belum diputar → reset ke step 0, aktifkan animasi
"""

from __future__ import annotations
from typing import Any

import dash
from dash import Input, Output, State, no_update, ALL
from dash.exceptions import PreventUpdate

from core.constants import FLOOR_NODES, PARKING_BLOCKS
from core.models import ParkingCondition
from core.runner import run_all
from core.animator import AlgorithmStep
from components.input_panel import RUN_BUTTON_ID, ALGO_TAB_ID, INPUT_CHECKLIST_ID
from components.graph_panel import (
    GRAPH_CYTO_ID, INTERVAL_ID, FRAME_STORE_ID, FRAME_INDEX_ID,
    build_cytoscape_elements,
)
from components.result_section import (
    RESULT_CARDS_ID, RESULT_TABLES_ID,
    build_result_cards_row, build_result_tables_row,
)

ANIMATION_INTERVAL_MS: int = 600

# ID panel deskripsi langkah — didefinisikan di sini agar layout bisa import

STEP_DESC_ID   = "display-step-description"
STEP_INFO_ID   = "display-step-info"

# Helpers: input

def _collect_full_blocks(checklist_values: list[list[str] | None]) -> set[str]:
    result: set[str] = set()
    for values in (checklist_values or []):
        if values:
            result.update(values)
    return result

# Helpers: serialisasi ke dcc.Store 

def _serialize_steps(steps: list[AlgorithmStep]) -> list[dict]:
    return [
        {
            "current_node":  s.current_node,
            "visited_nodes": list(s.visited_nodes),
            "path_nodes":    s.path_nodes,
            "description":   s.description,
        }
        for s in steps
    ]

def _serialize_search_result(algo_result: Any) -> dict:
    r = algo_result.result
    if not r.is_found:
        return {"is_found": False, "elapsed": r.elapsed_seconds}

    nearest  = r.nearest_block
    use_hops = hasattr(nearest, "total_hops")
    metric   = "total_hops" if use_hops else "total_cost"

    return {
        "is_found":     True,
        "block_id":     nearest.block_id,
        "metric_key":   metric,
        "metric_value": getattr(nearest, metric),
        "path":         nearest.path_from_entrance,
        "all_blocks": [
            {
                "block_id":     info.block_id,
                "metric_key":   metric,
                "metric_value": getattr(info, metric),
                "path":         info.path_from_entrance,
            }
            for info in r.all_reachable_blocks
        ],
        "elapsed": r.elapsed_seconds,
    }

def _build_store_data(full_blocks: set[str], all_results: dict) -> dict:
    return {
        "full_blocks": list(full_blocks),
        "algorithms": {
            key: {
                "search":  _serialize_search_result(ar),
                "steps":   _serialize_steps(ar.trace.steps),
                "path":    ar.trace.final_path,
            }
            for key, ar in all_results.items()
        },
    }

# Helpers: render Cytoscape

def _condition_from_store(store_data: dict) -> ParkingCondition:
    return ParkingCondition(full_blocks=set(store_data.get("full_blocks", [])))

def _deserialize_step(step_dict: dict) -> AlgorithmStep:
    return AlgorithmStep(
        current_node  = step_dict["current_node"],
        visited_nodes = set(step_dict["visited_nodes"]),
        path_nodes    = step_dict["path_nodes"],
        description   = step_dict["description"],
    )

def _render_step(
    store_data:  dict,
    active_tab:  str,
    step_index:  int | None,
    is_final:    bool = False,
) -> list[dict]:
    condition  = _condition_from_store(store_data)
    algo_data  = store_data["algorithms"].get(active_tab, {})
    steps      = algo_data.get("steps", [])
    final_path = algo_data.get("path", [])

    if step_index is None or not steps:
        return build_cytoscape_elements(condition)

    safe_index = min(step_index, len(steps) - 1)
    step       = _deserialize_step(steps[safe_index])

    return build_cytoscape_elements(
        condition  = condition,
        step       = step,
        final_path = final_path,
        is_final   = is_final,
    )

def _get_step_info(algo_data: dict, step_index: int) -> tuple[str, str]:
    steps = algo_data.get("steps", [])
    if not steps:
        return "Jalankan algoritma untuk melihat animasi.", ""

    safe_index  = min(step_index, len(steps) - 1)
    description = steps[safe_index].get("description", "")
    step_info   = f"Langkah {safe_index + 1} dari {len(steps)}"
    return description, step_info

# Register callbacks

def register_callbacks(app: dash.Dash) -> None:

    # 1. Tombol Run All → jalankan algoritma, simpan ke store, reset animasi
    @app.callback(
        Output(FRAME_STORE_ID,   "data"),
        Output(FRAME_INDEX_ID,   "data"),
        Output(INTERVAL_ID,      "disabled"),
        Output(RESULT_CARDS_ID,  "children"),
        Output(RESULT_TABLES_ID, "children"),
        Input(RUN_BUTTON_ID,     "n_clicks"),
        State({
            "type":  INPUT_CHECKLIST_ID,
            "floor": ALL,
        }, "value"),
        prevent_initial_call=True,
    )
    def on_run_all(n_clicks, checklist_values):
        if not n_clicks:
            raise PreventUpdate

        full_blocks     = _collect_full_blocks(checklist_values)
        all_results_obj = run_all(full_blocks)
        all_results     = all_results_obj.as_dict()

        store_data  = _build_store_data(full_blocks, all_results)
        frame_index = {"bfs": 0, "dijkstra": 0, "astar": 0}

        search_results = {k: v.result for k, v in all_results.items()}
        cards_row      = build_result_cards_row(search_results)
        tables_row     = build_result_tables_row(search_results)

        return store_data, frame_index, False, cards_row, tables_row

    # 2. Interval tick → maju satu langkah di tab aktif
    @app.callback(
        Output(GRAPH_CYTO_ID,  "elements"),
        Output(FRAME_INDEX_ID, "data",             allow_duplicate=True),
        Output(INTERVAL_ID,    "disabled",         allow_duplicate=True),
        Output(STEP_DESC_ID,   "children"),
        Output(STEP_INFO_ID,   "children"),
        Input(INTERVAL_ID,     "n_intervals"),
        State(FRAME_STORE_ID,  "data"),
        State(FRAME_INDEX_ID,  "data"),
        State(ALGO_TAB_ID,     "active_tab"),
        prevent_initial_call=True,
    )
    def on_animation_tick(n_intervals, store_data, frame_index, active_tab):
        if not store_data or not frame_index:
            raise PreventUpdate

        active_tab  = active_tab or "bfs"
        algo_data   = store_data["algorithms"].get(active_tab, {})
        steps       = algo_data.get("steps", [])
        current_idx = frame_index.get(active_tab, 0)

        if current_idx >= len(steps):
            return no_update, no_update, True, no_update, no_update

        is_final = (current_idx == len(steps) - 1)
        elements = _render_step(store_data, active_tab, current_idx, is_final)
        desc, info = _get_step_info(algo_data, current_idx)

        new_index = {**frame_index, active_tab: current_idx + 1}
        is_done   = (current_idx + 1) >= len(steps)

        return elements, new_index, is_done, desc, info

    # 3. Tab switch → render state yang tepat untuk tab yang dipilih
    @app.callback(
        Output(GRAPH_CYTO_ID,  "elements",         allow_duplicate=True),
        Output(FRAME_INDEX_ID, "data",             allow_duplicate=True),
        Output(INTERVAL_ID,    "disabled",         allow_duplicate=True),
        Output(STEP_DESC_ID,   "children",         allow_duplicate=True),
        Output(STEP_INFO_ID,   "children",         allow_duplicate=True),
        Input(ALGO_TAB_ID,     "active_tab"),
        State(FRAME_STORE_ID,  "data"),
        State(FRAME_INDEX_ID,  "data"),
        prevent_initial_call=True,
    )
    def on_tab_switch(active_tab, store_data, frame_index):
        if not store_data:
            raise PreventUpdate

        algo_data   = store_data["algorithms"].get(active_tab, {})
        steps       = algo_data.get("steps", [])
        current_idx = (frame_index or {}).get(active_tab, 0)
        is_done     = len(steps) > 0 and current_idx >= len(steps)

        if is_done:
            # Tab sudah selesai → tampilkan frame terakhir dengan path highlight
            elements      = _render_step(store_data, active_tab, len(steps) - 1, is_final=True)
            desc, info    = _get_step_info(algo_data, len(steps) - 1)
            return elements, no_update, True, desc, info

        # Tab belum diputar → reset ke step 0 dan mulai animasi
        new_index = {**(frame_index or {}), active_tab: 0}
        elements  = _render_step(store_data, active_tab, None)
        desc      = "Animasi dimulai..."
        info      = f"0 dari {len(steps)}" if steps else ""

        return elements, new_index, False, desc, info