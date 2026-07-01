"""
core/constants.py

Satu sumber kebenaran untuk semua konstanta proyek.
Re-export dari SearchBFS (sebagai referensi tunggal) agar seluruh layer UI
tidak pernah import langsung dari src/.
"""

from src.SearchBFS import (
    ENTRANCE_NODE,
    FLOOR_NODES,
    PARKING_BLOCKS,
    ENTRANCE_TO_FLOOR_WEIGHTS,
    BLOCK_INDEX_TO_WEIGHT,
)

# Label tampilan per algoritma
ALGORITHM_LABELS: dict[str, str] = {
    "bfs":      "BFS",
    "dijkstra": "Dijkstra",
    "astar":    "A*",
}

ALGORITHM_KEYS: list[str] = list(ALGORITHM_LABELS.keys())

# Warna aksen per algoritma — dipakai di tab, kartu hasil, dan tabel ranking
ALGORITHM_COLORS: dict[str, str] = {
    "bfs":      "#3B82F6",   # biru
    "dijkstra": "#10B981",   # hijau
    "astar":    "#F59E0B",   # oranye
}

# Warna node Cytoscape — dipakai di graph_panel dan legend
NODE_COLORS: dict[str, str] = {
    "entrance": "#6366F1",   # ungu  — pintu masuk
    "floor":    "#94A3B8",   # abu   — node lantai
    "available":"#34D399",   # hijau — blok tersedia
    "full":     "#1E1E2E",   # hitam — blok penuh (tetap tampil, tanpa edge)
    "visited":  "#93C5FD",   # biru muda — dikunjungi algoritma
    "current":  "#60A5FA",   # biru terang — node yang sedang diproses
    "path":     "#F97316",   # oranye — jalur terpilih
    "target":   "#4ADE80",   # hijau terang — blok tujuan akhir
}

# Konversi waktu
MS_PER_SECOND: float = 1_000.0