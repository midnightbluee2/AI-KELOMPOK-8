from __future__ import annotations

import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

import networkx as nx

# Konstanta
ENTRANCE_NODE = "ENTRANCE"
FLOOR_NODES = ["A", "B", "C", "D"]

PARKING_BLOCKS: dict[str, list[str]] = {
    "A": ["A1", "A2", "A3", "A4", "A5"],
    "B": ["B1", "B2", "B3", "B4", "B5"],
    "C": ["C1", "C2", "C3", "C4", "C5"],
    "D": ["D1", "D2", "D3", "D4", "D5"],
}

ENTRANCE_TO_FLOOR_WEIGHTS: dict[str, float] = {
    "A": 10.0,
    "B": 20.0,
    "C": 30.0,
    "D": 40.0,
}

BLOCK_INDEX_TO_WEIGHT: dict[int, float] = {
    1: 5.0,
    2: 6.0,
    3: 7.0,
    4: 8.0,
    5: 9.0,
}

# Model data
# Status ketersediaan blok parkir (penuh/tersedia)
@dataclass
class ParkingCondition:
    full_blocks: set[str]

    def is_block_available(self, block_id: str) -> bool:
        return block_id not in self.full_blocks

    def get_available_block_ids(self) -> set[str]:
        all_blocks = {block for blocks in PARKING_BLOCKS.values() for block in blocks}
        return all_blocks - self.full_blocks

# Hasil hop ke blok parkir tertentu dari pintu masuk (ENTRANCE)
@dataclass
class BlockHopInfo:
    block_id: str
    total_hops: int
    path_from_entrance: list[str]

# Hasil pencarian BFS
@dataclass
class SearchResult:
    nearest_block: Optional[BlockHopInfo]
    all_reachable_blocks: list[BlockHopInfo]
    elapsed_seconds: float

    @property
    def is_found(self) -> bool:
        return self.nearest_block is not None

# Pembangun graf
# Bobot edge lantai ke blok didasarkan pada nomor urut blok (A1=5, A2=6, ..., D5=9)
def resolve_block_weight(block_id: str) -> float:
    block_index = int(block_id[-1])
    return BLOCK_INDEX_TO_WEIGHT[block_index]

# Membangun graf berdasarkan kondisi parkir saat ini (blok penuh/tersedia)
def build_parking_graph(available_blocks: set[str]) -> nx.Graph:
    graph = nx.Graph()

    for floor_id in FLOOR_NODES:
        floor_weight = ENTRANCE_TO_FLOOR_WEIGHTS[floor_id]
        graph.add_edge(ENTRANCE_NODE, floor_id, weight=floor_weight)

        for block_id in PARKING_BLOCKS[floor_id]:
            if block_id not in available_blocks:
                continue
            block_weight = resolve_block_weight(block_id)
            graph.add_edge(floor_id, block_id, weight=block_weight)

    return graph

# Identifikasi node
def is_parking_block_node(node_id: str) -> bool:
    """Mengembalikan True jika node_id adalah blok parkir (bukan lantai atau entrance)."""
    return node_id not in FLOOR_NODES and node_id != ENTRANCE_NODE

# Algoritma BFS
def run_bfs_from_entrance(graph: nx.Graph) -> SearchResult:
    start_time = time.perf_counter()

    visited: set[str] = set()
    exploration_queue: deque[tuple[str, list[str]]] = deque()

    exploration_queue.append((ENTRANCE_NODE, [ENTRANCE_NODE]))
    visited.add(ENTRANCE_NODE)

    nearest_block: Optional[BlockHopInfo] = None
    all_reachable_blocks: list[BlockHopInfo] = []

    while exploration_queue:
        current_node_id, current_path = exploration_queue.popleft()

        if is_parking_block_node(current_node_id):
            hop_info = BlockHopInfo(
                block_id=current_node_id,
                total_hops=len(current_path) - 1,
                path_from_entrance=current_path,
            )
            all_reachable_blocks.append(hop_info)

            if nearest_block is None:
                nearest_block = hop_info
            # BFS tidak berhenti di blok pertama, lanjut kumpulkan semua blok
            continue

        for neighbor_id in graph.neighbors(current_node_id):
            # BFS mengabaikan bobot; graph[u][v]["weight"] tersedia untuk Dijkstra/A*
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                exploration_queue.append((neighbor_id, current_path + [neighbor_id]))

    elapsed = time.perf_counter() - start_time

    all_reachable_blocks.sort(key=lambda info: (info.total_hops, info.block_id))

    return SearchResult(
        nearest_block=nearest_block,
        all_reachable_blocks=all_reachable_blocks,
        elapsed_seconds=elapsed,
    )

# Tampilan terminal
# Menampilkan semua edge beserta bobotnya (untuk verifikasi graf yang dibangun)
def display_graph_edges(graph: nx.Graph) -> None:
    print("\n[GRAPH EDGES & WEIGHTS]")
    for node_a, node_b, data in sorted(graph.edges(data=True)):
        print(f"{node_a:10} — {node_b:4}  (weight: {data['weight']})")

# Menampilkan peta parkir dengan status setiap blok (TERSEDIA/PENUH)
def display_parking_map(condition: ParkingCondition) -> None:
    print("\nPETA PARKIR SAAT INI")
    print("=" * 36)
    print(f"{'LANTAI':<10} {'BLOK':<6} {'STATUS'}")
    print("-" * 36)
    for floor_id in FLOOR_NODES:
        floor_label = f"Lantai {floor_id}"
        for block_id in PARKING_BLOCKS[floor_id]:
            status_label = "[ TERSEDIA ]" if condition.is_block_available(block_id) else "[  PENUH   ]"
            print(f"{floor_label:<10} {block_id:<6} {status_label}")
        print("-" * 36)

# Menampilkan blok terdekat dan ranking semua blok berdasarkan hop dari ENTRANCE
def display_nearest_block(result: SearchResult) -> None:
    print("\n[SIMULASI: Cari blok parkir terdekat dari pintu masuk]")
    if not result.is_found:
        print("Tidak ada blok parkir yang tersedia.")
        print(f"Waktu pencarian : {result.elapsed_seconds * 1_000:.4f} ms")
        return

    info = result.nearest_block
    path_display = " → ".join(info.path_from_entrance)
    print(f"Blok terdekat   : {info.block_id}")
    print(f"Jumlah hop      : {info.total_hops}")
    print(f"Jalur           : {path_display}")
    print(f"Waktu pencarian : {result.elapsed_seconds * 1_000:.4f} ms")

# Menampilkan ranking semua blok berdasarkan hop dari ENTRANCE
def display_block_ranking(result: SearchResult) -> None:
    print("\n[RANKING BLOK berdasarkan hop dari ENTRANCE]")
    if not result.all_reachable_blocks:
        print("Tidak ada blok yang dapat dijangkau.")
        return

    for rank, info in enumerate(result.all_reachable_blocks, start=1):
        path_display = " → ".join(info.path_from_entrance)
        print(f"#{rank:2}  {info.block_id}  hops={info.total_hops}  path: {path_display}")

# Menampilkan hasil lengkap (blok terdekat + ranking semua blok)
def display_full_result(result: SearchResult) -> None:
    display_nearest_block(result)
    display_block_ranking(result)

# Mode interaktif (dengan input pengguna)
def prompt_full_blocks() -> set[str]:
    all_block_ids = {block for blocks in PARKING_BLOCKS.values() for block in blocks}

    print()
    print("Daftar semua blok parkir:")
    for floor_id in FLOOR_NODES:
        block_list = ", ".join(PARKING_BLOCKS[floor_id])
        print(f"Lantai {floor_id}: {block_list}")

    print()
    print("Masukkan blok yang PENUH (pisahkan dengan spasi atau koma).")
    print("Contoh: A1 A2 B3   atau   a1, a2, b3")
    print("Tekan Enter tanpa input jika semua blok tersedia.")
    print()

    raw_input = input("Blok penuh > ").strip()

    if not raw_input:
        return set()

    tokens = raw_input.replace(",", " ").upper().split()

    full_blocks: set[str] = set()
    invalid_tokens: list[str] = []

    for token in tokens:
        if token in all_block_ids:
            full_blocks.add(token)
        else:
            invalid_tokens.append(token)

    if invalid_tokens:
        print(f"\n[!] Blok tidak dikenal diabaikan: {', '.join(invalid_tokens)}")

    return full_blocks

def run_interactive_mode() -> None:
    print("\n" + "=" * 50)
    print("PARKING LOT FINDER — BFS ALGORITHM")
    print("Mode: Interaktif")
    print("=" * 50)

    while True:
        full_blocks = prompt_full_blocks()
        condition = ParkingCondition(full_blocks=full_blocks)

        display_parking_map(condition)

        graph = build_parking_graph(condition.get_available_block_ids())
        display_graph_edges(graph)

        result = run_bfs_from_entrance(graph)
        display_full_result(result)

        print("\nCari lagi dengan kondisi berbeda? (y/n)")
        again = input("> ").strip().lower()
        if again != "y":
            break

    print("\nProgram selesai.\n")

# Mode demo (tanpa input pengguna)
def run_demo_mode() -> None:
    print("\n" + "=" * 50)
    print("PARKING LOT FINDER — BFS ALGORITHM")
    print("Mode: Demo")
    print("=" * 50)

    demo_scenarios: list[tuple[str, set[str]]] = [
        ("Semua blok tersedia",  set()),
        ("Lantai A penuh",       {"A1", "A2", "A3", "A4", "A5"}),
        ("Lantai A dan B penuh", {"A1","A2","A3","A4","A5","B1","B2","B3","B4","B5"}),
        ("Hanya D5 tersisa",     {"A1","A2","A3","A4","A5","B1","B2","B3","B4","B5",
                                  "C1","C2","C3","C4","C5","D1","D2","D3","D4"}),
        ("Semua blok penuh",     {"A1","A2","A3","A4","A5","B1","B2","B3","B4","B5",
                                  "C1","C2","C3","C4","C5","D1","D2","D3","D4","D5"}),
    ]

    for scenario_name, full_blocks in demo_scenarios:
        print(f"\n{'='*50}")
        print(f"Skenario: {scenario_name}")
        print(f"{'='*50}")

        condition = ParkingCondition(full_blocks=full_blocks)
        display_parking_map(condition)

        graph = build_parking_graph(condition.get_available_block_ids())
        display_graph_edges(graph)

        result = run_bfs_from_entrance(graph)
        display_full_result(result)

# Entry point
if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo_mode()
    else:
        run_interactive_mode()