"""
algorithms/
-----------
Package adapter yang menjembatani algoritma asli (SearchBFS.py, SearchDijkstra.py)
dengan lapisan GUI (Streamlit dan Dash).

Ekspor utama yang digunakan GUI:
    - ParkingCondition  : model kondisi parkir
    - SearchResult      : model hasil pencarian
    - AlgorithmStep     : model satu langkah animasi
    - build_parking_graph : membangun graf dari kondisi parkir
    - run_bfs           : menjalankan BFS dan menghasilkan SearchResult
    - run_dijkstra      : menjalankan Dijkstra dan menghasilkan SearchResult
    - NODE_COLORS       : palet warna node untuk visualisasi
    - PARKING_BLOCKS    : peta lantai ke blok
    - FLOOR_NODES       : urutan lantai
    - ENTRANCE_NODE     : ID node pintu masuk
"""

from algorithms.constants import (
    ENTRANCE_NODE,
    FLOOR_NODES,
    PARKING_BLOCKS,
    NODE_COLORS,
)
from algorithms.models import ParkingCondition, SearchResult, AlgorithmStep
from algorithms.graph_builder import build_parking_graph
from algorithms.search_bfs import run_bfs
from algorithms.search_dijkstra import run_dijkstra

__all__ = [
    "ENTRANCE_NODE",
    "FLOOR_NODES",
    "PARKING_BLOCKS",
    "NODE_COLORS",
    "ParkingCondition",
    "SearchResult",
    "AlgorithmStep",
    "build_parking_graph",
    "run_bfs",
    "run_dijkstra",
]