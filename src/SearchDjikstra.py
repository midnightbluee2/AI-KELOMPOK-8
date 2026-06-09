import networkx as nx
import heapq

#  BUILD GRAPH
G = nx.Graph()

# Root = lantai (A=1, B=2, C=3, D=4)
floors = {"A": 1, "B": 2, "C": 3, "D": 4}
for floor, w in floors.items():
    G.add_edge("ROOT", floor, weight=w)

# Lantai = slot (X1..X5, weight mulai dari 5)
for floor in floors:
    for i in range(1, 6):
        slot = f"{floor}{i}"
        slot_weight = 4 + i          # A1=5, A2=6, ... A5=9 (dst. sama tiap lantai)
        G.add_edge(floor, slot, weight=slot_weight)

#  DIJKSTRA (manual, tanpa nx bawaan)

def dijkstra(graph, start):
    dist   = {node: float("inf") for node in graph.nodes}
    prev   = {node: None         for node in graph.nodes}
    dist[start] = 0

    pq = [(0, start)]          # (cost, node)
    visited = set()

    while pq:
        cost, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        for v, data in graph[u].items():
            w = data["weight"]
            if cost + w < dist[v]:
                dist[v] = cost + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))

    return dist, prev

def reconstruct_path(prev, target):
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    return list(reversed(path))

#  MAIN
def main():
    print("=" * 50)
    print("  SMART PARKING — Dijkstra Algorithm")
    print("=" * 50)

    # Semua node beserta edge-nya
    print("\n[GRAPH EDGES & WEIGHTS]")
    for u, v, data in sorted(G.edges(data=True)):
        print(f"  {u:6} — {v:4}  (weight: {data['weight']})")

    # Jalankan Dijkstra dari ROOT
    dist, prev = dijkstra(G, "ROOT")

    print("\n[SHORTEST DISTANCE dari ROOT ke setiap node]")
    for node in sorted(dist):
        path = reconstruct_path(prev, node)
        print(f"  {node:4}  cost={dist[node]:2}   path: {' → '.join(path)}")

    # Simulasi: cari slot terdekat dari ROOT 
    print("\n[SIMULASI: Cari slot parkir terdekat dari pintu masuk]")
    all_slots = [n for n in G.nodes if len(n) == 2 and n[0].isalpha() and n[1].isdigit()]
    best_slot = min(all_slots, key=lambda s: dist[s])
    best_path = reconstruct_path(prev, best_slot)

    print(f"  Slot terdekat : {best_slot}")
    print(f"  Total cost    : {dist[best_slot]}")
    print(f"  Jalur         : {' → '.join(best_path)}")

    # Tampilkan semua slot diurutkan by cost
    print("\n[RANKING SLOT berdasarkan jarak dari ROOT]")
    ranked = sorted(all_slots, key=lambda s: dist[s])
    for rank, slot in enumerate(ranked, 1):
        path = reconstruct_path(prev, slot)
        print(f"  #{rank:2}  {slot}  cost={dist[slot]}  path: {' → '.join(path)}")

if __name__ == "__main__":
    main()