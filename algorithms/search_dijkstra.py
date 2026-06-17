"""
search_dijkstra.py
------------------
Adapter untuk algoritma Dijkstra yang menambahkan kemampuan step-by-step
tracking tanpa mengubah file SearchDijkstra.py asli (milik anggota tim lain).

Cara kerja:
- Fungsi `run_dijkstra()` memanggil algoritma asli untuk mendapatkan hasil akhir.
- Fungsi `trace_dijkstra_steps()` menjalankan ulang Dijkstra secara internal
  untuk menghasilkan AlgorithmStep per langkah, khusus kebutuhan animasi GUI.

Dengan pendekatan ini, perubahan apapun di SearchDijkstra.py oleh pemiliknya
tidak akan merusak GUI selama signature fungsi utamanya tidak berubah.
"""

from __future__ import annotations

import sys
import os
import heapq

import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from SearchDjikstra import (  # noqa: E402
    run_dijkstra_from_entrance as _run_dijkstra_original,
    is_parking_block_node,
)
from algorithms.constants import ENTRANCE_NODE
from algorithms.models import AlgorithmStep, SearchResult


def run_dijkstra(graph: nx.Graph) -> SearchResult:
    """
    Menjalankan Dijkstra dan mengemas hasilnya ke dalam SearchResult standar.

    Memanggil fungsi asli `run_dijkstra_from_entrance` dari SearchDijkstra.py,
    lalu mengkonversi hasilnya ke model SearchResult yang dipakai GUI.

    Args:
        graph: Graf parkir yang sudah dibangun via graph_builder.

    Returns:
        SearchResult berisi blok terdekat, jalur, metrik, dan langkah animasi.
    """
    original_result = _run_dijkstra_original(graph)
    steps = trace_dijkstra_steps(graph)

    nearest_id   = original_result.nearest_block.block_id if original_result.is_found else None
    nearest_path = original_result.nearest_block.path_from_entrance if original_result.is_found else []
    nearest_cost = original_result.nearest_block.total_cost if original_result.is_found else 0.0

    all_visited = {step.current_node for step in steps}

    return SearchResult(
        nearest_block_id   = nearest_id,
        nearest_block_path = nearest_path,
        nearest_block_cost = nearest_cost,
        all_visited_nodes  = all_visited,
        all_steps          = steps,
        elapsed_ms         = original_result.elapsed_seconds * 1_000,
        algorithm_name     = "Dijkstra",
    )


def trace_dijkstra_steps(graph: nx.Graph) -> list[AlgorithmStep]:
    """
    Menjalankan ulang Dijkstra secara internal untuk menghasilkan jejak langkah.

    Fungsi ini TIDAK mengubah logika Dijkstra asli. Ia mereplikasi mekanisme
    priority queue dan path reconstruction untuk merekam setiap langkah
    sebagai AlgorithmStep, khusus kebutuhan animasi GUI.

    Args:
        graph: Graf parkir yang sudah dibangun.

    Returns:
        List AlgorithmStep yang merepresentasikan tiap iterasi Dijkstra.
    """
    steps: list[AlgorithmStep] = []

    dist: dict[str, float]           = {node: float("inf") for node in graph.nodes}
    prev: dict[str, str | None]      = {node: None for node in graph.nodes}
    visited: set[str]                = set()
    priority_queue: list[tuple[float, str]] = [(0.0, ENTRANCE_NODE)]

    dist[ENTRANCE_NODE] = 0.0

    while priority_queue:
        current_cost, current_node = heapq.heappop(priority_queue)

        if current_node in visited:
            continue
        visited.add(current_node)

        current_path = _reconstruct_path(prev, current_node)
        description  = _build_step_description(current_node, current_cost, current_path)

        steps.append(AlgorithmStep(
            visited_nodes = set(visited),
            current_node  = current_node,
            current_path  = current_path,
            description   = description,
        ))

        for neighbor, edge_data in graph[current_node].items():
            edge_weight    = edge_data["weight"]
            new_cost       = current_cost + edge_weight

            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = current_node
                heapq.heappush(priority_queue, (new_cost, neighbor))

    return steps


def _reconstruct_path(prev: dict[str, str | None], target_node: str) -> list[str]:
    """
    Merekonstruksi jalur dari ENTRANCE ke target_node menggunakan tabel prev.

    Args:
        prev        : Dict yang memetakan tiap node ke node pendahulunya.
        target_node : Node tujuan yang jalurnya ingin direkonstruksi.

    Returns:
        List node dari ENTRANCE hingga target_node secara berurutan.
    """
    path: list[str] = []
    node: str | None = target_node

    while node is not None:
        path.append(node)
        node = prev[node]

    return list(reversed(path))


def _build_step_description(
    current_node: str,
    current_cost: float,
    current_path: list[str],
) -> str:
    """
    Membangun teks deskripsi untuk satu langkah Dijkstra.

    Deskripsi ini ditampilkan di panel informasi GUI saat mode step-by-step.

    Args:
        current_node : Node yang sedang diproses.
        current_cost : Total cost yang terakumulasi hingga node ini.
        current_path : Jalur dari ENTRANCE ke current_node.

    Returns:
        String deskripsi yang siap ditampilkan.
    """
    path_str  = " → ".join(current_path)
    node_type = "blok parkir" if is_parking_block_node(current_node) else "node lantai/entrance"

    return (
        f"Mengunjungi {node_type} **{current_node}** "
        f"(cost={current_cost}) | Jalur: {path_str}"
    )