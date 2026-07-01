"""
core/runner.py

Satu titik eksekusi untuk menjalankan ketiga algoritma sekaligus.
Menghasilkan SearchResult (dari src/) dan TraceResult (dari animator)
per algoritma, lalu mengemasnya dalam AllResults.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.models import ParkingCondition, build_parking_graph, SearchResult
from core.animator import TraceResult, trace_bfs, trace_dijkstra, trace_astar
from src.SearchBFS import run_bfs_from_entrance
from src.SearchDjikstra import run_dijkstra_from_entrance
from src.SearchAStar import run_astar_from_entrance

@dataclass(frozen=True)
class AlgoResult:
    """Hasil satu algoritma: SearchResult (logika) + TraceResult (animasi)."""
    result: SearchResult
    trace:  TraceResult = field(default_factory=TraceResult)

@dataclass(frozen=True)
class AllResults:
    bfs:      AlgoResult
    dijkstra: AlgoResult
    astar:    AlgoResult

    def as_dict(self) -> dict[str, AlgoResult]:
        return {
            "bfs":      self.bfs,
            "dijkstra": self.dijkstra,
            "astar":    self.astar,
        }

def run_all(full_block_ids: set[str]) -> AllResults:
    condition = ParkingCondition(full_blocks=full_block_ids)
    available = condition.get_available_block_ids()
    graph     = build_parking_graph(available)

    return AllResults(
        bfs=AlgoResult(
            result=run_bfs_from_entrance(graph),
            trace=trace_bfs(graph),
        ),
        dijkstra=AlgoResult(
            result=run_dijkstra_from_entrance(graph),
            trace=trace_dijkstra(graph),
        ),
        astar=AlgoResult(
            result=run_astar_from_entrance(graph),
            trace=trace_astar(graph),
        ),
    )