"""
search_bfs.py
-------------
Adapter untuk algoritma BFS yang menambahkan kemampuan step-by-step tracking
tanpa mengubah file SearchBFS.py asli.

Cara kerja:
- Fungsi `run_bfs()` memanggil algoritma asli untuk mendapatkan hasil akhir.
- Fungsi `trace_bfs_steps()` menjalankan ulang BFS secara internal untuk
  menghasilkan AlgorithmStep per langkah, khusus kebutuhan animasi GUI.

Pemisahan ini menjaga file asli tetap bersih sekaligus memberi GUI
kemampuan animasi yang dibutuhkan.
"""

from __future__ import annotations

import sys
import os
import time
from collections import deque

import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from SearchBFS import (  # noqa: E402
    run_bfs_from_entrance as _run_bfs_original,
    is_parking_block_node,
)
from algorithms.constants import ENTRANCE_NODE
from algorithms.models import AlgorithmStep, SearchResult


def run_bfs(graph: nx.Graph) -> SearchResult:
    """
    Menjalankan BFS dan mengemas hasilnya ke dalam SearchResult standar.

    Memanggil fungsi asli `run_bfs_from_entrance` dari SearchBFS.py,
    lalu mengkonversi hasilnya ke model SearchResult yang dipakai GUI.

    Args:
        graph: Graf parkir yang sudah dibangun via graph_builder.

    Returns:
        SearchResult berisi blok terdekat, jalur, metrik, dan langkah animasi.
    """
    original_result = _run_bfs_original(graph)
    steps = trace_bfs_steps(graph)

    nearest_id   = original_result.nearest_block.block_id if original_result.is_found else None
    nearest_path = original_result.nearest_block.path_from_entrance if original_result.is_found else []
    nearest_cost = float(original_result.nearest_block.total_hops) if original_result.is_found else 0.0

    all_visited = {step.current_node for step in steps}

    return SearchResult(
        nearest_block_id   = nearest_id,
        nearest_block_path = nearest_path,
        nearest_block_cost = nearest_cost,
        all_visited_nodes  = all_visited,
        all_steps          = steps,
        elapsed_ms         = original_result.elapsed_seconds * 1_000,
        algorithm_name     = "BFS",
    )


def trace_bfs_steps(graph: nx.Graph) -> list[AlgorithmStep]:
    """
    Menjalankan ulang BFS secara internal untuk menghasilkan jejak langkah.

    Fungsi ini TIDAK mengubah logika BFS asli. Ia hanya merekam kondisi
    antrian dan node yang dikunjungi di setiap iterasi, lalu mengemasnya
    sebagai list AlgorithmStep untuk keperluan animasi GUI.

    Args:
        graph: Graf parkir yang sudah dibangun.

    Returns:
        List AlgorithmStep yang merepresentasikan tiap iterasi BFS.
    """
    steps: list[AlgorithmStep] = []
    visited: set[str] = set()
    queue: deque[tuple[str, list[str]]] = deque()

    queue.append((ENTRANCE_NODE, [ENTRANCE_NODE]))
    visited.add(ENTRANCE_NODE)

    while queue:
        current_node, current_path = queue.popleft()

        description = _build_step_description(current_node, current_path)
        steps.append(AlgorithmStep(
            visited_nodes = set(visited),
            current_node  = current_node,
            current_path  = list(current_path),
            description   = description,
        ))

        if is_parking_block_node(current_node):
            continue

        for neighbor in graph.neighbors(current_node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, current_path + [neighbor]))

    return steps


def _build_step_description(current_node: str, current_path: list[str]) -> str:
    """
    Membangun teks deskripsi untuk satu langkah BFS.

    Deskripsi ini ditampilkan di panel informasi GUI saat mode step-by-step.

    Args:
        current_node : Node yang sedang diproses.
        current_path : Jalur dari ENTRANCE ke current_node.

    Returns:
        String deskripsi yang siap ditampilkan.
    """
    hop_count   = len(current_path) - 1
    path_str    = " → ".join(current_path)
    node_type   = "blok parkir" if is_parking_block_node(current_node) else "node lantai/entrance"

    return (
        f"Mengunjungi {node_type} **{current_node}** "
        f"(hop ke-{hop_count}) | Jalur: {path_str}"
    )