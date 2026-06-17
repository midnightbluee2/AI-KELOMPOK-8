"""
gui_streamlit/app.py — Visualisasi BFS untuk sistem parkir.

Cara menjalankan:
    cd src
    streamlit run gui-streamlit/app.py
"""

import sys
import os
import time

import streamlit as st
import plotly.graph_objects as go
import networkx as nx

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from algorithms import (
    ENTRANCE_NODE,
    FLOOR_NODES,
    PARKING_BLOCKS,
    NODE_COLORS,
    ParkingCondition,
    SearchResult,
    AlgorithmStep,
    build_parking_graph,
    run_bfs,
)

# --- Konstanta UI ---

PAGE_TITLE      = "BFS — Parking Lot Finder"
GRAPH_HEIGHT_PX = 520
AUTO_PLAY_DELAY_OPTIONS = {
    "Lambat (1.5 detik)": 1.5,
    "Normal (0.8 detik)": 0.8,
    "Cepat (0.3 detik)":  0.3,
}

# Posisi tetap tiap node agar graf tidak bergeser saat animasi
NODE_POSITIONS: dict[str, tuple[float, float]] = {
    "ENTRANCE": (0.0, 0.0),
    "A": (1.0, 1.5),  "B": (1.0, 0.5),  "C": (1.0, -0.5), "D": (1.0, -1.5),
    "A1": (2.5, 2.2), "A2": (2.5, 1.8), "A3": (2.5, 1.4), "A4": (2.5, 1.0), "A5": (2.5, 0.7),
    "B1": (2.5, 0.3), "B2": (2.5, 0.0), "B3": (2.5,-0.3), "B4": (2.5,-0.6), "B5": (2.5,-0.9),
    "C1": (2.5,-1.2), "C2": (2.5,-1.5), "C3": (2.5,-1.8), "C4": (2.5,-2.1), "C5": (2.5,-2.4),
    "D1": (2.5,-2.7), "D2": (2.5,-3.0), "D3": (2.5,-3.3), "D4": (2.5,-3.6), "D5": (2.5,-3.9),
}

# --- Session state ---

def initialize_session_state() -> None:
    """Inisialisasi session state; dipanggil sekali saat halaman dimuat."""
    defaults = {
        "full_blocks":   set(),
        "search_result": None,
        "current_step":  0,
        "is_playing":    False,
        "search_done":   False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- Sidebar ---

def render_sidebar() -> ParkingCondition:
    """Render sidebar toggle blok parkir; returns ParkingCondition."""
    st.sidebar.title("🅿️ Kondisi Parkir")
    st.sidebar.caption("Centang blok yang **penuh** (tidak tersedia).")

    full_blocks: set[str] = set()

    for floor_id in FLOOR_NODES:
        st.sidebar.markdown(f"**Lantai {floor_id}**")
        cols = st.sidebar.columns(5)
        for idx, block_id in enumerate(PARKING_BLOCKS[floor_id]):
            with cols[idx]:
                if st.checkbox(block_id, key=f"block_{block_id}"):
                    full_blocks.add(block_id)

    st.sidebar.divider()
    if st.sidebar.button("🔍 Jalankan BFS", use_container_width=True, type="primary"):
        _trigger_search(full_blocks)

    return ParkingCondition(full_blocks=full_blocks)


def _trigger_search(full_blocks: set[str]) -> None:
    """Jalankan BFS baru dan simpan hasilnya ke session state."""
    condition = ParkingCondition(full_blocks=full_blocks)
    graph     = build_parking_graph(condition.get_available_block_ids())
    result    = run_bfs(graph)

    st.session_state.full_blocks   = full_blocks
    st.session_state.search_result = result
    st.session_state.current_step  = 0
    st.session_state.is_playing    = False
    st.session_state.search_done   = True


# --- Metrik ---

def render_metrics(result: SearchResult) -> None:
    """Render panel metrik: algoritma, blok terdekat, hop, node dikunjungi, waktu, jalur."""
    st.subheader("📊 Hasil Pencarian")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Algoritma", result.algorithm_name)
    with col2:
        st.metric("Blok Terdekat", result.nearest_block_id if result.is_found else "Tidak ada")
    with col3:
        st.metric("Jumlah Hop", int(result.nearest_block_cost) if result.is_found else "-")
    with col4:
        st.metric("Node Dikunjungi", result.total_visited)

    col5, col6 = st.columns(2)
    with col5:
        st.metric("Waktu Pencarian", f"{result.elapsed_ms:.4f} ms")
    with col6:
        st.metric("Panjang Jalur", result.path_display)


# --- Visualisasi graf ---

def resolve_node_color(
    node_id: str,
    condition: ParkingCondition,
    visited_nodes: set[str],
    current_node: str,
    result: SearchResult,
) -> str:
    """
    Tentukan warna node berdasarkan statusnya pada langkah saat ini.
    Prioritas: current > jalur akhir > dikunjungi > penuh > entrance > lantai > tersedia.
    """
    if node_id == current_node:
        return NODE_COLORS["visited"]
    if node_id in result.nearest_block_path and result.is_found:
        return NODE_COLORS["path"]
    if node_id in visited_nodes:
        return "#F0A500"  # oranye muda: sudah dikunjungi tapi bukan current
    if node_id == ENTRANCE_NODE:
        return NODE_COLORS["entrance"]
    if node_id in FLOOR_NODES:
        return NODE_COLORS["floor"]
    if node_id in condition.full_blocks:
        return NODE_COLORS["full"]
    return NODE_COLORS["available"]


def build_graph_figure(
    graph: nx.Graph,
    condition: ParkingCondition,
    result: SearchResult,
    step: AlgorithmStep,
) -> go.Figure:
    """Bangun figure Plotly untuk graf parkir pada satu langkah animasi."""
    edge_traces = _build_edge_traces(graph)
    node_trace  = _build_node_trace(graph, condition, result, step)

    return go.Figure(
        data   = edge_traces + [node_trace],
        layout = go.Layout(
            title        = dict(text="Graf Parkir — BFS", font=dict(size=16)),
            height       = GRAPH_HEIGHT_PX,
            showlegend   = False,
            hovermode    = "closest",
            margin       = dict(l=20, r=20, t=50, b=20),
            xaxis        = dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis        = dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor = "rgba(0,0,0,0)",
            paper_bgcolor= "rgba(0,0,0,0)",
        ),
    )


def _build_edge_traces(graph: nx.Graph) -> list[go.Scatter]:
    """Bangun trace Plotly untuk semua edge (garis + label bobot)."""
    traces: list[go.Scatter] = []

    for node_a, node_b, data in graph.edges(data=True):
        x_a, y_a = NODE_POSITIONS.get(node_a, (0, 0))
        x_b, y_b = NODE_POSITIONS.get(node_b, (0, 0))
        weight    = data["weight"]

        traces.append(go.Scatter(
            x=[x_a, x_b, None], y=[y_a, y_b, None],
            mode="lines", line=dict(width=1.5, color="#AAAAAA"), hoverinfo="none",
        ))
        traces.append(go.Scatter(
            x=[(x_a + x_b) / 2], y=[(y_a + y_b) / 2],
            mode="text", text=[str(weight)],
            textfont=dict(size=9, color="#888888"), hoverinfo="none",
        ))

    return traces


def _build_node_trace(
    graph: nx.Graph,
    condition: ParkingCondition,
    result: SearchResult,
    step: AlgorithmStep,
) -> go.Scatter:
    """Bangun trace Plotly untuk semua node dengan warna sesuai status animasi."""
    x_coords, y_coords, colors, labels, hovers = [], [], [], [], []

    for node_id in graph.nodes():
        x, y  = NODE_POSITIONS.get(node_id, (0, 0))
        color = resolve_node_color(node_id, condition, step.visited_nodes, step.current_node, result)

        x_coords.append(x)
        y_coords.append(y)
        colors.append(color)
        labels.append(node_id)
        hovers.append(f"<b>{node_id}</b>")

    return go.Scatter(
        x=x_coords, y=y_coords,
        mode="markers+text",
        marker=dict(size=22, color=colors, line=dict(width=2, color="#FFFFFF")),
        text=labels, textfont=dict(size=10, color="#FFFFFF"),
        textposition="middle center",
        hovertext=hovers, hoverinfo="text",
    )


# --- Kontrol animasi ---

def render_animation_controls(result: SearchResult) -> None:
    """Render tombol Reset, Prev, Next, dan Auto-play."""
    total_steps = len(result.all_steps)
    st.caption(f"Langkah {st.session_state.current_step + 1} dari {total_steps}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("⏮ Reset", use_container_width=True):
            st.session_state.current_step = 0
            st.session_state.is_playing   = False
    with col2:
        if st.button("◀ Prev", disabled=st.session_state.current_step <= 0, use_container_width=True):
            st.session_state.current_step -= 1
    with col3:
        if st.button("Next ▶", disabled=st.session_state.current_step >= total_steps - 1, use_container_width=True):
            st.session_state.current_step += 1
    with col4:
        if st.button("⏸ Stop" if st.session_state.is_playing else "▶ Auto", use_container_width=True):
            st.session_state.is_playing = not st.session_state.is_playing


def run_auto_play(result: SearchResult, delay_seconds: float) -> None:
    """Maju satu langkah per interval, lalu rerun halaman."""
    total_steps = len(result.all_steps)

    if st.session_state.current_step >= total_steps - 1:
        st.session_state.is_playing = False
        return

    time.sleep(delay_seconds)
    st.session_state.current_step += 1

    if st.session_state.current_step >= total_steps - 1:
        st.session_state.is_playing = False

    st.rerun()


# --- Entry point ---

def render_page() -> None:
    """Fungsi utama: render seluruh halaman Streamlit."""
    st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon="🅿️")
    initialize_session_state()

    condition = render_sidebar()

    st.title("🅿️ Parking Lot Finder — BFS")
    st.caption(
        "BFS (Breadth-First Search) mencari blok parkir terdekat berdasarkan "
        "**jumlah hop** (bukan bobot edge). Setiap langkah, BFS mengunjungi "
        "semua tetangga sebelum maju lebih dalam."
    )

    if not st.session_state.search_done:
        st.info("👈 Atur kondisi parkir di sidebar, lalu klik **Jalankan BFS**.")
        return

    result: SearchResult = st.session_state.search_result
    graph  = build_parking_graph(condition.get_available_block_ids())

    render_metrics(result)
    st.divider()

    speed_label = st.select_slider(
        "Kecepatan Auto-play",
        options=list(AUTO_PLAY_DELAY_OPTIONS.keys()),
        value="Normal (0.8 detik)",
    )
    delay = AUTO_PLAY_DELAY_OPTIONS[speed_label]

    render_animation_controls(result)

    current_step_index = min(st.session_state.current_step, len(result.all_steps) - 1)
    current_step: AlgorithmStep = result.all_steps[current_step_index]

    st.info(f"🔍 {current_step.description}")

    figure = build_graph_figure(graph, condition, result, current_step)
    st.plotly_chart(figure, use_container_width=True)

    _render_color_legend()

    if st.session_state.is_playing:
        run_auto_play(result, delay)


def _render_color_legend() -> None:
    """Render legenda warna node di bawah graf."""
    st.markdown("**Legenda Warna Node:**")
    cols = st.columns(6)
    legend_items = [
        (NODE_COLORS["entrance"],  "ENTRANCE"),
        (NODE_COLORS["floor"],     "Lantai"),
        (NODE_COLORS["available"], "Tersedia"),
        (NODE_COLORS["full"],      "Penuh"),
        (NODE_COLORS["visited"],   "Dikunjungi"),
        (NODE_COLORS["path"],      "Jalur Akhir"),
    ]
    for col, (color, label) in zip(cols, legend_items):
        with col:
            st.markdown(
                f'<span style="background:{color};padding:4px 10px;'
                f'border-radius:8px;color:white;font-size:12px">{label}</span>',
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    render_page()