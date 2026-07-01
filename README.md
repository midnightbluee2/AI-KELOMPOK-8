# Smart Parking - Perbandingan Algoritma Searching

> **AI-KELOMPOK-8:**
> Perbandingan Algoritma Searching Pada Sistem Smart Parking Motor di Mall The Park Solo

## Anggota Kelompok

| NIM | Nama |
|---|---|
| L0124123 | Wiwid Widyaningsih |
| L0124129 | Alena Mashia Qolby |

---

## Deskripsi Proyek

Proyek ini mensimulasikan sistem **Smart Parking** yang merekomendasikan slot parkir motor terdekat dari pintu masuk (ENTRANCE) menggunakan tiga algoritma pencarian graf:

- **BFS** (Breadth-First Search) : mencari slot berdasarkan jumlah hop terkecil
- **Dijkstra** : mencari slot berdasarkan akumulasi cost terkecil
- **A\*** (A-Star) : mencari slot berdasarkan f = g + h (cost nyata + estimasi heuristik)

Ketiga algoritma divisualisasikan secara animasi step-by-step dalam satu dashboard interaktif berbasis **Dash** dan **Cytoscape**, sehingga perbedaan perilaku traversal masing-masing algoritma dapat diamati secara langsung.

Studi kasus menggunakan struktur parkir 4 lantai (A, B, C, D) dengan masing-masing 5 slot parkir (X1–X5), mengacu pada layout gedung parkir Mall The Park Solo.

---

## Struktur Graf Parkir

```
                        ENTRANCE
              /        /        \        \
            A(10)   B(20)     C(30)    D(40)
           / | \ \ \
         A1  A2 A3 A4 A5
        (1) (2)(3)(4)(5)
```

Bobot edge:
- **ENTRANCE → Lantai**: A=10, B=20, C=30, D=40 (semakin jauh dari pintu masuk, semakin besar)
- **Lantai → Blok**: X1=1, X2=2, X3=3, X4=4, X5=5 (semakin jauh dari tangga lantai, semakin besar)

---

## Fitur Aplikasi

- Pilih blok yang sedang **penuh** melalui checklist per lantai
- Jalankan ketiga algoritma sekaligus dengan tombol **Run All**
- Animasi traversal step-by-step di graph Cytoscape per tab algoritma
- Panel deskripsi yang menjelaskan setiap langkah iterasi algoritma
- Kartu ringkasan hasil (blok terdekat + cost/hop + waktu eksekusi)
- Tabel ranking seluruh blok yang dapat dijangkau dari ENTRANCE

---

## Struktur Direktori

```
smart-parking/
├── app.py                      # Entry point (jalankan dari sini)
├── layout.py                   # Perakitan layout Dash
├── requirements.txt
│
├── src/                        # Implementasi algoritma murni (tidak dimodifikasi)
│   ├── SearchBFS.py
│   ├── SearchDjikstra.py
│   └── SearchAStar.py
│
├── core/                       # Layer adapter antara src/ dan UI
│   ├── constants.py            # Satu sumber konstanta (re-export dari src/)
│   ├── models.py               # ParkingCondition, build_parking_graph
│   ├── animator.py             # Step tracer per algoritma untuk animasi
│   └── runner.py               # Eksekusi ketiga algoritma sekaligus
│
├── components/                 # Komponen UI Dash
│   ├── graph_panel.py          # Graph Cytoscape + legend
│   ├── input_panel.py          # Checklist blok penuh + tombol Run
│   ├── result_card.py          # Kartu ringkasan satu algoritma
│   └── result_section.py       # Baris kartu + tabel ranking
│
└── callbacks/
    └── run_callback.py         # Callback animasi, tab switch, Run All
```

---

## Cara Menjalankan

### 1. Clone atau ekstrak proyek

```bash
git clone https://github.com/midnightbluee2/AI-KELOMPOK-8
cd AI-KELOMPOK-8
```

### 2. Install dependensi

```bash
pip install -r requirements.txt
```

### 3. Jalankan aplikasi

```bash
python app.py
```

### 4. Buka di browser

```
http://localhost:8050
```

---

## Dependensi

| Package | Versi minimum | Kegunaan |
|---|---|---|
| `dash` | ≥ 2.16.0 | Framework web interaktif |
| `dash-bootstrap-components` | ≥ 1.5.0 | Komponen UI (grid, card, tab) |
| `dash-cytoscape` | ≥ 1.0.0 | Visualisasi graf interaktif |
| `networkx` | ≥ 3.2 | Representasi dan operasi graf |

---

## Cara Menggunakan Dashboard

1. **Pilih blok penuh** : centang slot parkir yang sedang terisi penuh di panel kiri. Blok yang dipilih akan tampil berwarna gelap di graf tanpa edge (tidak bisa dilewati algoritma).
2. **Klik Run All** : ketiga algoritma dijalankan sekaligus. Animasi otomatis dimulai dari tab BFS.
3. **Amati animasi** : setiap langkah traversal divisualisasikan dengan warna:
   - 🟣 Ungu: ENTRANCE
   - ⚫ Hitam: Blok penuh
   - 🔵 Biru muda: Node yang sudah dikunjungi
   - 🔵 Biru terang: Node yang sedang diproses
   - 🟠 Oranye: Jalur terpilih
   - 🟢 Hijau terang: Blok tujuan akhir
4. **Ganti tab** : klik tab Dijkstra atau A* untuk melihat animasi algoritma lain. Tab yang sudah selesai akan langsung menampilkan jalur akhir.
5. **Baca hasil** : kartu dan tabel di bawah graph menampilkan blok terdekat, cost, dan ranking seluruh blok yang dapat dijangkau.
