from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Optional
import heapq

import networkx as nx

#Konstanta
ENTRANCE_NODE = "ENTRANCE"
FLOOR_NODES = ["A", "B", "C", "D"]

PARKING_BLOCKS: dict[str, list[str]] = {
    "A": ["A1", "A2", "A3", "A4", "A5"],
    "B": ["B1", "B2", "B3", "B4", "B5"],
    "C": ["C1", "C2", "C3", "C4", "C5"],
    "D": ["D1", "D2", "D3", "D4", "D5"],
}

ENTRANCE_TO_FLOOR_WEIGHTS: dict[str, float] = {
    "A": 1.0,
    "B": 2.0,
    "C": 3.0,
    "D": 4.0,
}

BLOCK_INDEX_TO_WEIGHT: dict[int, float] = {
    1: 5.0,
    2: 6.0,
    3: 7.0,
    4: 8.0,
    5: 9.0,
}

#  Model data
@dataclass
class ParkingCondition:
    full_blocks: set[str]

    def is_block_available(self, block_id: str) -> bool:
        return block_id not in self.full_blocks

    def get_available_block_ids(self) -> set[str]:
        all_blocks = {block for blocks in PARKING_BLOCKS.values() for block in blocks}
        return all_blocks - self.full_blocks


@dataclass
class BlockCostInfo:
    block_id: str
    total_cost: float
    path_from_entrance: list[str]


@dataclass
class SearchResult:
    nearest_block: Optional[BlockCostInfo]
    all_reachable_blocks: list[BlockCostInfo]
    elapsed_seconds: float

    @property
    def is_found(self) -> bool:
        return self.nearest_block is not None


# graf
def resolve_block_weight(block_id: str) -> float:
    block_index = int(block_id[-1])
    return BLOCK_INDEX_TO_WEIGHT[block_index]


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
    return node_id not in FLOOR_NODES and node_id != ENTRANCE_NODE


# Algoritma Dijkstra
def run_dijkstra_from_entrance(graph: nx.Graph) -> SearchResult:
    start_time = time.perf_counter()

    dist: dict[str, float] = {node: float("inf") for node in graph.nodes}
    prev: dict[str, Optional[str]] = {node: None for node in graph.nodes}
    dist[ENTRANCE_NODE] = 0.0

    pq: list[tuple[float, str]] = [(0.0, ENTRANCE_NODE)]
    visited: set[str] = set()

    while pq:
        # ambil node dengan cost terkcil dan hapus
        cost, u = heapq.heappop(pq) 
        if u in visited:
            continue
        visited.add(u)

        for v, data in graph[u].items():
            w: float = data["weight"]
            if cost + w < dist[v]:
                # jumlah total jarak
                dist[v] = cost + w 
                prev[v] = u
                # masuk ke pq
                heapq.heappush(pq, (dist[v], v))

    # jalur
    def reconstruct_path(target: str) -> list[str]:
        path: list[str] = []
        node: Optional[str] = target
        while node is not None:
            path.append(node)
            node = prev[node]
        return list(reversed(path))

    # Kumpulkan semua blok yang dapat dijangkau
    all_reachable_blocks: list[BlockCostInfo] = []
    for node_id in graph.nodes:
        if is_parking_block_node(node_id) and dist[node_id] < float("inf"):
            all_reachable_blocks.append(
                BlockCostInfo(
                    block_id=node_id,
                    total_cost=dist[node_id],
                    path_from_entrance=reconstruct_path(node_id),
                )
            )

    all_reachable_blocks.sort(key=lambda info: (info.total_cost, info.block_id))

    nearest_block = all_reachable_blocks[0] if all_reachable_blocks else None
    elapsed = time.perf_counter() - start_time

    return SearchResult(
        nearest_block=nearest_block,
        all_reachable_blocks=all_reachable_blocks,
        elapsed_seconds=elapsed,
    )


# Tampilan terminal

#tampilan edge dan bobotnya
def display_graph_edges(graph: nx.Graph) -> None:
    print("\nGRAPH EDGES & WEIGHTS")
    for node_a, node_b, data in sorted(graph.edges(data=True)):
        print(f"{node_a:10} — {node_b:4}  (weight: {data['weight']})")

#tampilan peta parkir nya
def display_parking_map(condition: ParkingCondition) -> None:
    print("\nPETA PARKIR SAAT INI")
    print("")
    print(f"{'LANTAI':<10} {'BLOK':<6} {'STATUS'}")
    print("-" * 36)
    for floor_id in FLOOR_NODES:
        floor_label = f"Lantai {floor_id}"
        for block_id in PARKING_BLOCKS[floor_id]:
            status_label = (
                "[ TERSEDIA ]"
                if condition.is_block_available(block_id)
                else "[  PENUH   ]"
            )
            print(f"{floor_label:<10} {block_id:<6} {status_label}")
        print("-" * 36)

#tampilan blok terdekat
def display_nearest_block(result: SearchResult) -> None:
    print("\nSIMULASI: Hasil blok terdekat")
    if not result.is_found:
        print("Tidak ada blok parkir yang tersedia.")
        print(f"Waktu pencarian : {result.elapsed_seconds * 1_000:.4f} ms")
        return

    info = result.nearest_block
    path_display = " - ".join(info.path_from_entrance)
    print(f"Blok terdekat   : {info.block_id}")
    print(f"Total cost      : {info.total_cost}")
    print(f"Jalur           : {path_display}")
    print(f"Waktu pencarian : {result.elapsed_seconds * 1_000:.4f} ms")

#urutan based on cost di semua blok
def display_block_ranking(result: SearchResult) -> None:
    print("\nUrutan BLOK berdasarkan cost dari ENTRANCE")
    if not result.all_reachable_blocks:
        print("Tidak ada blok yang dapat dijangkau.")
        return

    for rank, info in enumerate(result.all_reachable_blocks, start=1):
        path_display = " - ".join(info.path_from_entrance)
        print(f"{rank:2}  {info.block_id}  cost={info.total_cost}  path: {path_display}")


def display_full_result(result: SearchResult) -> None:
    display_nearest_block(result)
    display_block_ranking(result)

#input user
def prompt_full_blocks() -> set[str]:
    all_block_ids = {block for blocks in PARKING_BLOCKS.values() for block in blocks}

    print()
    print("Daftar semua blok parkir:")
    for floor_id in FLOOR_NODES:
        block_list = ", ".join(PARKING_BLOCKS[floor_id])
        print(f"Lantai {floor_id}: {block_list}")

    print()
    print("Masukkan blok yang penuh (pisahkan dengan spasi atau koma).")
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
        print(f"\n Note: Blok tidak dikenal diabaikan: {', '.join(invalid_tokens)}")

    return full_blocks

#output user
def run_interactive_mode() -> None:
    print("SMART PARKING")

    while True:
        full_blocks = prompt_full_blocks()
        condition = ParkingCondition(full_blocks=full_blocks)

        display_parking_map(condition)

        graph = build_parking_graph(condition.get_available_block_ids())
        display_graph_edges(graph)

        result = run_dijkstra_from_entrance(graph)
        display_full_result(result)

        print("\nCari lagi dengan kondisi berbeda? (y/n)")
        again = input("> ").strip().lower()
        if again != "y":
            break

    print("\nProgram selesai.\n")


# demo
def run_demo_mode() -> None:
    print("SMART PARKING(DEMO)")

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
        print(f"Skenario: {scenario_name}")

        condition = ParkingCondition(full_blocks=full_blocks)
        display_parking_map(condition)

        graph = build_parking_graph(condition.get_available_block_ids())
        display_graph_edges(graph)

        result = run_dijkstra_from_entrance(graph)
        display_full_result(result)


# Entry point
if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo_mode()
    else:
        run_interactive_mode()