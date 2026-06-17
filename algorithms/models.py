"""
models.py
---------
Mendefinisikan semua model data (dataclass) yang digunakan bersama oleh
adapter BFS, adapter Dijkstra, dan kedua GUI.

Pemisahan model ke file ini menghindari duplikasi definisi yang sebelumnya
ada di SearchBFS.py dan SearchDijkstra.py secara terpisah.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from algorithms.constants import PARKING_BLOCKS


@dataclass
class ParkingCondition:
    """
    Merepresentasikan kondisi parkir saat ini.

    Attributes:
        full_blocks: Kumpulan ID blok yang sedang penuh (tidak tersedia).
    """
    full_blocks: set[str] = field(default_factory=set)

    def is_block_available(self, block_id: str) -> bool:
        """Mengembalikan True jika blok dengan ID tersebut tidak penuh."""
        return block_id not in self.full_blocks

    def get_available_block_ids(self) -> set[str]:
        """Mengembalikan semua ID blok yang saat ini tersedia (tidak penuh)."""
        all_block_ids = {
            block_id
            for blocks in PARKING_BLOCKS.values()
            for block_id in blocks
        }
        return all_block_ids - self.full_blocks

    def get_all_block_ids(self) -> set[str]:
        """Mengembalikan seluruh ID blok tanpa memperhatikan status ketersediaan."""
        return {
            block_id
            for blocks in PARKING_BLOCKS.values()
            for block_id in blocks
        }


@dataclass
class AlgorithmStep:
    """
    Merepresentasikan satu langkah eksekusi algoritma pencarian.
    Digunakan untuk animasi step-by-step pada GUI.

    Attributes:
        visited_nodes : Kumpulan node yang sudah dikunjungi sampai langkah ini.
        current_node  : Node yang sedang diproses pada langkah ini.
        current_path  : Jalur dari ENTRANCE menuju current_node.
        description   : Penjelasan singkat tentang apa yang terjadi di langkah ini.
    """
    visited_nodes: set[str]
    current_node: str
    current_path: list[str]
    description: str


@dataclass
class SearchResult:
    """
    Merepresentasikan hasil akhir pencarian (BFS maupun Dijkstra).

    Attributes:
        nearest_block_id    : ID blok parkir terdekat yang ditemukan.
        nearest_block_path  : Jalur dari ENTRANCE ke blok terdekat.
        nearest_block_cost  : Total cost atau jumlah hop ke blok terdekat.
        all_visited_nodes   : Semua node yang dikunjungi selama pencarian.
        all_steps           : Seluruh langkah eksekusi (untuk animasi).
        elapsed_ms          : Waktu pencarian dalam milidetik.
        algorithm_name      : Nama algoritma yang digunakan ("BFS" atau "Dijkstra").
    """
    nearest_block_id: Optional[str]
    nearest_block_path: list[str]
    nearest_block_cost: float
    all_visited_nodes: set[str]
    all_steps: list[AlgorithmStep]
    elapsed_ms: float
    algorithm_name: str

    @property
    def is_found(self) -> bool:
        """Mengembalikan True jika blok terdekat berhasil ditemukan."""
        return self.nearest_block_id is not None

    @property
    def path_display(self) -> str:
        """Mengembalikan jalur sebagai string yang siap ditampilkan di GUI."""
        return " → ".join(self.nearest_block_path) if self.nearest_block_path else "-"

    @property
    def total_visited(self) -> int:
        """Mengembalikan jumlah node yang dikunjungi selama pencarian."""
        return len(self.all_visited_nodes)