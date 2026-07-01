"""
core/models.py

Re-export dataclass dari src/ agar seluruh layer UI dan core
hanya bergantung ke satu titik import, bukan langsung ke src/.

Tidak ada logika tambahan di sini — hanya alias import.
"""

from src.SearchBFS import (
    ParkingCondition,
    BlockHopInfo,
    SearchResult,
    build_parking_graph,
    is_parking_block_node,
)

# BlockCostInfo dipakai oleh Dijkstra & A* (berbeda dari BlockHopInfo di BFS)
from src.SearchDjikstra import BlockCostInfo

__all__ = [
    "ParkingCondition",
    "BlockHopInfo",
    "BlockCostInfo",
    "SearchResult",
    "build_parking_graph",
    "is_parking_block_node",
]