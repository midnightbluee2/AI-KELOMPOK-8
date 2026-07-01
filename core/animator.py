"""
core/animator.py

Menghasilkan jejak langkah (step trace) dari setiap algoritma pencarian,
untuk dipakai animasi step-by-step di graph_panel berbasis Cytoscape.

Setiap algoritma dijalankan ulang secara internal di sini — bukan
menggunakan hasil akhir dari src/ — agar setiap iterasi dapat direkam
sebagai satu AlgorithmStep yang akurat.

Tidak ada perubahan pada logika algoritma di src/. File ini hanya
mereplikasi mekanisme traversal masing-masing algoritma untuk kebutuhan
animasi.
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field

import networkx as nx

from core.constants import ENTRANCE_NODE, FLOOR_NODES

# Model langkah animasi 

@dataclass
class AlgorithmStep:
    current_node:  str
    visited_nodes: set[str]         = field(default_factory=set)
    path_nodes:    list[str]        = field(default_factory=list)
    description:   str              = ""

@dataclass
class TraceResult:
    steps:      list[AlgorithmStep]
    final_path: list[str] = field(default_factory=list)

# Helpers

def _is_block_node(node_id: str) -> bool:
    return node_id not in FLOOR_NODES and node_id != ENTRANCE_NODE

def _reconstruct_path(prev: dict[str, str | None], target: str) -> list[str]:
    path: list[str] = []
    node: str | None = target
    while node is not None:
        path.append(node)
        node = prev[node]
    return list(reversed(path))

# Tracer BFS

def trace_bfs(graph: nx.Graph) -> TraceResult:
    """
    Jalankan BFS dari ENTRANCE dan rekam setiap langkah iterasinya.

    BFS mengabaikan bobot edge; urutan kunjungan ditentukan oleh hop (jumlah edge).
    Blok pertama yang ditemukan adalah yang paling dekat dari ENTRANCE.

    Args:
        graph: Graf parkir yang sudah dibangun (hanya blok tersedia).

    Returns:
        TraceResult berisi semua langkah BFS dan jalur blok terdekat.
    """
    steps:   list[AlgorithmStep] = []
    visited: set[str]            = set()
    queue:   deque[tuple[str, list[str]]] = deque()

    queue.append((ENTRANCE_NODE, [ENTRANCE_NODE]))
    visited.add(ENTRANCE_NODE)

    final_path: list[str] = []

    while queue:
        current_node, current_path = queue.popleft()

        node_type   = "blok parkir" if _is_block_node(current_node) else "node lantai/entrance"
        hop_count   = len(current_path) - 1
        path_str    = " → ".join(current_path)
        description = (
            f"Mengunjungi {node_type} [{current_node}] "
            f"(hop ke-{hop_count}) | Jalur: {path_str}"
        )

        steps.append(AlgorithmStep(
            current_node  = current_node,
            visited_nodes = set(visited),
            path_nodes    = list(current_path),
            description   = description,
        ))

        if _is_block_node(current_node):
            if not final_path:
                final_path = list(current_path)
            continue

        for neighbor in graph.neighbors(current_node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, current_path + [neighbor]))

    return TraceResult(steps=steps, final_path=final_path)


# Tracer Dijkstra

def trace_dijkstra(graph: nx.Graph) -> TraceResult:
    """
    Jalankan Dijkstra dari ENTRANCE dan rekam setiap langkah iterasinya.

    Dijkstra memilih node dengan akumulasi cost terkecil via priority queue.
    Blok pertama yang di-pop dari queue adalah yang paling murah dari ENTRANCE.

    Args:
        graph: Graf parkir yang sudah dibangun (hanya blok tersedia).

    Returns:
        TraceResult berisi semua langkah Dijkstra dan jalur blok terdekat.
    """
    steps:   list[AlgorithmStep]         = []
    dist:    dict[str, float]            = {n: float("inf") for n in graph.nodes}
    prev:    dict[str, str | None]       = {n: None for n in graph.nodes}
    visited: set[str]                    = set()
    pq:      list[tuple[float, str]]     = [(0.0, ENTRANCE_NODE)]

    dist[ENTRANCE_NODE] = 0.0
    final_path: list[str] = []

    while pq:
        current_cost, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue
        visited.add(current_node)

        current_path = _reconstruct_path(prev, current_node)
        node_type    = "blok parkir" if _is_block_node(current_node) else "node lantai/entrance"
        path_str     = " → ".join(current_path)
        description  = (
            f"Mengunjungi {node_type} [{current_node}] "
            f"(cost={current_cost:.1f}) | Jalur: {path_str}"
        )

        steps.append(AlgorithmStep(
            current_node  = current_node,
            visited_nodes = set(visited),
            path_nodes    = current_path,
            description   = description,
        ))

        if _is_block_node(current_node) and not final_path:
            final_path = current_path

        for neighbor, edge_data in graph[current_node].items():
            new_cost = current_cost + edge_data["weight"]
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))

    return TraceResult(steps=steps, final_path=final_path)


# Tracer A*

def _heuristic(node_id: str) -> float:
    """
    Fungsi heuristik untuk A* — estimasi sisa cost dari node ke blok terdekat.

    Konsisten dengan heuristik di src/SearchAStar.py agar step trace
    mencerminkan perilaku algoritma asli.
    """
    from core.constants import ENTRANCE_TO_FLOOR_WEIGHTS, BLOCK_INDEX_TO_WEIGHT
    if _is_block_node(node_id):
        return 0.0
    if node_id in FLOOR_NODES:
        return BLOCK_INDEX_TO_WEIGHT[1]                                  # 5.0
    # ENTRANCE
    return min(ENTRANCE_TO_FLOOR_WEIGHTS.values()) + BLOCK_INDEX_TO_WEIGHT[1]  # 6.0


def trace_astar(graph: nx.Graph) -> TraceResult:
    """
    Jalankan A* dari ENTRANCE dan rekam setiap langkah iterasinya.

    A* menggunakan f = g + h (g: cost nyata, h: heuristik estimasi sisa).
    Node diproses berdasarkan f terkecil, sehingga lebih terarah dari Dijkstra.

    Args:
        graph: Graf parkir yang sudah dibangun (hanya blok tersedia).

    Returns:
        TraceResult berisi semua langkah A* dan jalur blok terdekat.
    """
    steps:   list[AlgorithmStep]     = []
    g_score: dict[str, float]        = {n: float("inf") for n in graph.nodes}
    prev:    dict[str, str | None]   = {n: None for n in graph.nodes}
    visited: set[str]                = set()
    pq:      list[tuple[float, str]] = [(_heuristic(ENTRANCE_NODE), ENTRANCE_NODE)]

    g_score[ENTRANCE_NODE] = 0.0
    final_path: list[str] = []

    while pq:
        f_cost, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue
        visited.add(current_node)

        g = g_score[current_node]
        h = _heuristic(current_node)
        current_path = _reconstruct_path(prev, current_node)
        node_type    = "blok parkir" if _is_block_node(current_node) else "node lantai/entrance"
        path_str     = " → ".join(current_path)
        description  = (
            f"Mengunjungi {node_type} [{current_node}] "
            f"(g={g:.1f}, h={h:.1f}, f={g+h:.1f}) | Jalur: {path_str}"
        )

        steps.append(AlgorithmStep(
            current_node  = current_node,
            visited_nodes = set(visited),
            path_nodes    = current_path,
            description   = description,
        ))

        if _is_block_node(current_node) and not final_path:
            final_path = current_path

        for neighbor, edge_data in graph[current_node].items():
            tentative_g = g + edge_data["weight"]
            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                prev[neighbor]    = current_node
                heapq.heappush(pq, (tentative_g + _heuristic(neighbor), neighbor))

    return TraceResult(steps=steps, final_path=final_path)