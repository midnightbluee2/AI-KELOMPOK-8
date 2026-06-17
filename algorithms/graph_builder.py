"""
graph_builder.py
----------------
Adapter tipis yang membungkus fungsi pembangun graf dari file algoritma asli.

File ini TIDAK menduplikasi logika pembuatan graf. Ia hanya menyediakan
antarmuka bersih agar GUI tidak perlu mengimport langsung dari SearchBFS.py
atau SearchDijkstra.py (yang memiliki dependensi berbeda-beda).
"""

from __future__ import annotations

import sys
import os

import networkx as nx

# Tambahkan folder src ke path agar SearchBFS dan SearchDijkstra bisa diimport
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from SearchBFS import build_parking_graph as _build_graph_from_bfs  # noqa: E402


def build_parking_graph(available_block_ids: set[str]) -> nx.Graph:
    """
    Membangun graf parkir berdasarkan blok yang tersedia.

    Mendelegasikan ke fungsi asli di SearchBFS.py karena kedua algoritma
    menggunakan graf dengan struktur yang identik.

    Args:
        available_block_ids: Kumpulan ID blok parkir yang tidak penuh.

    Returns:
        Graf NetworkX yang merepresentasikan layout parkir.
    """
    return _build_graph_from_bfs(available_block_ids)


def get_all_node_ids(graph: nx.Graph) -> list[str]:
    """
    Mengembalikan semua ID node dalam graf sebagai list.

    Berguna untuk GUI saat perlu melakukan iterasi semua node
    untuk menetapkan warna atau posisi visual.

    Args:
        graph: Graf parkir yang sudah dibangun.

    Returns:
        List berisi semua ID node dalam graf.
    """
    return list(graph.nodes())


def get_all_edges(graph: nx.Graph) -> list[tuple[str, str, float]]:
    """
    Mengembalikan semua edge dalam graf beserta bobotnya.

    Format return: list of tuple (node_a, node_b, weight).
    Berguna untuk GUI saat perlu menggambar edge dengan label bobot.

    Args:
        graph: Graf parkir yang sudah dibangun.

    Returns:
        List of tuple (node_a, node_b, weight).
    """
    return [
        (node_a, node_b, data["weight"])
        for node_a, node_b, data in graph.edges(data=True)
    ]