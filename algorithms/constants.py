"""
constants.py
------------
Satu-satunya sumber kebenaran (single source of truth) untuk semua konstanta
yang digunakan oleh GUI maupun adapter algoritma.

Dengan memusatkan konstanta di sini, perubahan nilai cukup dilakukan di satu
tempat tanpa harus menyentuh file algoritma asli maupun file GUI.
"""

# Node pintu masuk — titik awal semua pencarian
ENTRANCE_NODE: str = "ENTRANCE"

# Urutan lantai parkir (A = terdekat, D = terjauh dari pintu masuk)
FLOOR_NODES: list[str] = ["A", "B", "C", "D"]

# Peta lantai ke daftar blok parkir yang ada di lantai tersebut
PARKING_BLOCKS: dict[str, list[str]] = {
    "A": ["A1", "A2", "A3", "A4", "A5"],
    "B": ["B1", "B2", "B3", "B4", "B5"],
    "C": ["C1", "C2", "C3", "C4", "C5"],
    "D": ["D1", "D2", "D3", "D4", "D5"],
}

# Bobot edge dari ENTRANCE ke tiap lantai (semakin jauh lantai, semakin besar bobot)
ENTRANCE_TO_FLOOR_WEIGHTS: dict[str, float] = {
    "A": 1.0,
    "B": 2.0,
    "C": 3.0,
    "D": 4.0,
}

# Bobot edge dari lantai ke blok, berdasarkan nomor urut blok (1–5)
BLOCK_INDEX_TO_WEIGHT: dict[int, float] = {
    1: 5.0,
    2: 6.0,
    3: 7.0,
    4: 8.0,
    5: 9.0,
}

# Warna node untuk visualisasi GUI (shared antara Streamlit dan Dash)
NODE_COLORS = {
    "entrance":  "#4A90D9",   # biru  — pintu masuk
    "floor":     "#7B68EE",   # ungu  — node lantai
    "available": "#2ECC71",   # hijau — blok tersedia
    "full":      "#E74C3C",   # merah — blok penuh
    "visited":   "#F39C12",   # oranye — node yang sudah dikunjungi algoritma
    "path":      "#F1C40F",   # kuning — jalur akhir menuju blok terdekat
    "target":    "#1ABC9C",   # tosca  — blok parkir tujuan (hasil akhir)
}