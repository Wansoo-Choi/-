"""다익스트라 알고리즘 시뮬레이터.

실행: py -3.12 -m streamlit run streamlit_app.py
외부 데이터/API/추가 그래프 패키지 없이 동작합니다.
"""

from __future__ import annotations

import csv
import html
import io
import math
import random
import secrets
import time
from dataclasses import dataclass
from typing import Optional

import streamlit as st


@dataclass(frozen=True)
class Graph:
    nodes: tuple[str, ...]
    positions: dict[str, tuple[float, float]]
    edges: tuple[tuple[str, str, int], ...]
    seed: int

    def adjacency(self):
        result = {node: {} for node in self.nodes}
        for u, v, cost in self.edges:
            result[u][v] = cost
            result[v][u] = cost
        return result


@dataclass(frozen=True)
class Frame:
    kind: str
    title: str
    message: str
    distances: dict[str, float]
    parents: dict[str, Optional[str]]
    settled: frozenset[str]
    current: Optional[str]
    edge: Optional[tuple[str, str]]
    changed: Optional[str]
    checks: int
    updates: int
    formula: str = ""


def crosses(a, b, c, d):
    """공유 끝점 이외에서 두 선분이 엄격하게 교차하는지 검사합니다."""
    def turn(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return turn(a, b, c) * turn(a, b, d) < 0 and turn(c, d, a) * turn(c, d, b) < 0


def generate_graph(n=10, density="보통", low=1, high=20, seed=20261030):
    """무작위 연결 단순 무방향 그래프. 균등 무작위 그래프 표본은 아닙니다.

    흔들린 격자에 정점을 배치하고 무작위 신장 트리를 만든 후 간선을 추가합니다.
    가독성을 위해 짧은 간선을 선호하고 추가 간선의 교차를 피합니다.
    간선 비용은 위치와 독립적으로 [low, high]에서 균등하게 뽑습니다.
    """
    if not 8 <= n <= 12:
        raise ValueError("정점 수는 8~12개여야 합니다.")
    if not 1 <= low <= high <= 50:
        raise ValueError("비용은 1~50의 양의 정수여야 합니다.")
    factors = {"간결": 1.25, "보통": 1.75, "촘촘": 2.15}
    if density not in factors:
        raise ValueError("알 수 없는 간선 밀도입니다.")
    rng = random.Random(seed)
    nodes = tuple(chr(65 + i) for i in range(n))
    rows = math.ceil(n / 4)
    slots = []
    for i in range(n):
        row, col = divmod(i, 4)
        count = min(4, n - row * 4)
        x = 100 + col * 170 + (4 - count) * 85 + rng.uniform(-17, 17)
        y = 95 + row * (330 / (rows - 1)) + rng.uniform(-17, 17)
        slots.append((x, y))
    rng.shuffle(slots)
    positions = dict(zip(nodes, slots))
    pairs = [(u, v) for i, u in enumerate(nodes) for v in nodes[i + 1:]]

    def length(edge):
        p, q = (positions[v] for v in edge)
        return math.hypot(p[0] - q[0], p[1] - q[1])

    # 무작위로 흔든 길이순 Kruskal 방식으로 모든 정점을 잇는 트리를 만듭니다.
    # 이 생성용 길이와 최단경로 계산에 쓰는 정수 비용은 별개입니다.
    representatives = {v: v for v in nodes}

    def find(v):
        while representatives[v] != v:
            representatives[v] = representatives[representatives[v]]
            v = representatives[v]
        return v

    priority = {edge: length(edge) * rng.uniform(0.65, 1.4) for edge in pairs}
    chosen = []
    for u, v in sorted(pairs, key=lambda p: priority[p]):
        ru, rv = find(u), find(v)
        if ru != rv:
            representatives[ru] = rv
            chosen.append((u, v))
    target = min(len(pairs), round((n - 1) * factors[density]))
    candidates = [edge for edge in pairs if edge not in chosen]
    rank = {edge: length(edge) * rng.uniform(0.55, 1.6) for edge in candidates}
    for edge in sorted(candidates, key=lambda p: rank[p]):
        if len(chosen) >= target:
            break
        u, v = edge
        if any(
            len({u, v, a, b}) == 4
            and crosses(positions[u], positions[v], positions[a], positions[b])
            for a, b in chosen
        ):
            continue
        chosen.append(edge)
    edges = tuple((u, v, rng.randint(low, high)) for u, v in sorted(chosen))
    return Graph(nodes, positions, edges, seed)


def number(value):
    return "∞" if math.isinf(value) else str(int(value))


def dijkstra_frames(graph: Graph, source: str):
    """선형 탐색 다익스트라의 매 상태를 독립 스냅샷으로 기록합니다.

    각 미확정 이웃마다 '검사'와 '갱신/유지'를 분리하여 이전 값과 비교를 보여줍니다.
    동률인 최소 거리 정점은 이름의 사전순으로 확정합니다.
    """
    if source not in graph.nodes:
        raise ValueError("시작 정점이 그래프에 없습니다.")
    adjacency = graph.adjacency()
    if any(w <= 0 for row in adjacency.values() for w in row.values()):
        raise ValueError("이 앱에서는 양의 간선 비용만 허용합니다.")
    distances = {node: math.inf for node in graph.nodes}
    distances[source] = 0
    parents = {node: None for node in graph.nodes}
    settled = set()
    frames = []
    checks = updates = 0
    current = None

    def snapshot(kind, title, message, edge=None, changed=None, formula=""):
        frames.append(Frame(kind, title, message, distances.copy(), parents.copy(),
                            frozenset(settled), current, edge, changed, checks, updates, formula))

    snapshot("init", "시작할 준비가 되었습니다", f"시작점 {source}의 거리는 0, 나머지는 ∞입니다. 재생하거나 다음 단계로 이동하세요.")
    while len(settled) < len(graph.nodes):
        current = min((v for v in graph.nodes if v not in settled), key=lambda v: (distances[v], v))
        if math.isinf(distances[current]):
            break
        settled.add(current)
        snapshot("settle", f"{current}의 최단거리 확정", f"미확정 정점 중 거리 추정값이 최소인 {current}를 선택합니다. d({current}) = {number(distances[current])}은 이제 최단거리입니다.")
        for neighbor, cost in sorted(adjacency[current].items()):
            if neighbor in settled:
                continue
            checks += 1
            old = distances[neighbor]
            candidate = distances[current] + cost
            formula = f"d({current}) + cost({current}, {neighbor}) = {number(distances[current])} + {cost} = {number(candidate)}"
            snapshot("inspect", f"간선 {current} → {neighbor} 검사", f"{current}를 거쳐 {neighbor}로 가는 비용 {number(candidate)}을 기존 추정값 {number(old)}과 비교합니다.", (current, neighbor), formula=formula)
            if candidate < old:
                distances[neighbor] = candidate
                parents[neighbor] = current
                updates += 1
                snapshot("relax", f"{neighbor}의 거리 추정값 갱신", f"{number(candidate)} < {number(old)}이므로 d({neighbor})을 {number(old)}에서 {number(candidate)}으로 줄입니다. 이전 정점은 {current}입니다.", (current, neighbor), neighbor, f"{number(candidate)} < {number(old)}  →  d({neighbor}) = {number(candidate)}")
            else:
                snapshot("keep", f"{neighbor}의 기존 추정값 유지", f"새 비용 {number(candidate)}은 기존 추정값 {number(old)}보다 작지 않습니다. 거리와 이전 정점을 유지합니다.", (current, neighbor), formula=f"{number(candidate)} ≥ {number(old)}  →  갱신 없음")
    current = None
    if len(settled) == len(graph.nodes):
        message = f"모든 {len(graph.nodes)}개 정점의 최단거리가 확정되었습니다. 파란 간선이 최단경로 트리입니다. 도착점을 골라 개별 경로도 확인하세요."
    else:
        message = "도달 가능한 모든 정점을 확정했습니다. 나머지 정점까지의 거리는 ∞입니다."
    snapshot("done", "모든 최단경로 계산 완료", message)
    return frames


def path_to(parents, source, target):
    path, seen = [], set()
    node = target
    while node is not None and node not in seen:
        path.append(node)
        if node == source:
            return list(reversed(path))
        seen.add(node)
        node = parents[node]
    return []


CSS = """
<style>
html, body, [class*="st-"] {font-family:'Noto Sans KR',sans-serif;}
.stApp {background:#f6f8fc;color:#14233b;}
.block-container {max-width:1510px;padding-top:2.2rem;padding-bottom:2rem;}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #e4eaf2;}
[data-testid="stSidebar"] .block-container {padding-top:2rem;}
.eyebrow {font-size:11px;font-weight:800;color:#2773ee;letter-spacing:2.4px;margin-bottom:8px;}
.app-title {font-size:clamp(26px,3vw,38px);font-weight:800;letter-spacing:-1.8px;line-height:1.3;margin:0 0 10px;}
.subtitle {color:#63728b;font-size:14px;line-height:1.8;margin-bottom:20px;}
.section-label {font-size:12px;font-weight:800;letter-spacing:1.2px;color:#63728b;margin:16px 0 10px;}
.metric-row {display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:10px 0 22px;}
.metric-card {border:1px solid #e1e8f2;background:#fff;border-radius:14px;padding:14px 18px;}
.metric-card small {font-size:11px;color:#68788e;display:block;margin-bottom:5px;}
.metric-card strong {font-size:25px;letter-spacing:-1px;}
.metric-card span {font-size:12px;color:#8794a7;margin-left:5px;}
.board {background:#101e34;border-radius:18px;overflow:hidden;border:1px solid #21324e;}
.board-head {display:flex;justify-content:space-between;padding:18px 22px 0;color:#dce7fa;font-size:13px;font-weight:700;}
.board-head span {color:#8195b7;font-size:11px;font-weight:400;}
.legend {display:flex;gap:15px;flex-wrap:wrap;padding:5px 22px 18px;color:#bbc9df;font-size:11px;}
.legend i {display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;}
.panel {background:#fff;border:1px solid #e1e8f2;border-radius:16px;padding:18px 20px;margin-bottom:12px;}
.phase {font-size:10px;letter-spacing:1.6px;color:#2c73e8;font-weight:800;margin-bottom:7px;}
.event-title {font-size:20px;font-weight:800;margin-bottom:10px;letter-spacing:-.5px;}
.event-text {font-size:13px;color:#5b6d86;line-height:1.8;min-height:66px;}
.formula {background:#eef4ff;border-left:3px solid #377ff0;padding:11px 12px;margin-top:12px;font-size:12px;font-weight:600;line-height:1.7;border-radius:4px;}
.distance-table {width:100%;border-collapse:collapse;font-size:12px;}
.distance-table th {text-align:left;color:#8390a5;font-weight:500;font-size:10px;padding:7px 5px;border-bottom:1px solid #e6ecf5;}
.distance-table td {padding:7px 5px;border-bottom:1px solid #f0f3f8;}
.distance-table tr.active {background:#fff5dc;}
.distance-table tr.changed {background:#e7faf3;}
.distance-table .done {color:#237b67;font-size:10px;}
.distance-table .pending {color:#8591a3;font-size:10px;}
.path-pill {background:#f2edff;border:1px solid #dcd0fd;color:#6342b6;border-radius:10px;padding:12px 16px;margin:8px 0 14px;font-size:13px;}
.queue {display:flex;gap:7px;flex-wrap:wrap;margin-top:10px;}
.queue span {background:#f0f4fa;border:1px solid #dfe6f0;border-radius:7px;padding:4px 8px;font-size:11px;color:#435774;}
.queue span:first-child {background:#eaf2ff;border-color:#a7c7ff;color:#1e63c9;}
div.stButton>button {border-radius:9px;min-height:42px;font-weight:600;}
div.stButton>button[kind="primary"] {background:#2673ec;border-color:#2673ec;}
[data-testid="stProgressBar"] {margin-top:8px;}
.footnote {font-size:11px;color:#8492a7;line-height:1.8;margin-top:20px;}
.guide-heading {font-size:19px;font-weight:800;margin:0 0 12px;letter-spacing:-.5px;}
.guide-text {font-size:13px;line-height:1.9;color:#52647f;}
.guide-text p {margin:0 0 12px;}
.guide-text ol,.guide-text ul {padding-left:20px;margin:8px 0;}
.guide-text li {margin-bottom:9px;}
.guide-text b {color:#203b60;}
.guide-note {background:#f1f5fb;border-radius:9px;padding:11px 13px;font-size:12px;line-height:1.8;color:#516787;margin-top:12px;}
.roadmap-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px;}
.roadmap-card {background:#fff;border:1px solid #dfe7f1;border-radius:15px;padding:20px;}
.roadmap-card .number {color:#2b75ed;font-size:12px;font-weight:800;letter-spacing:1px;}
.roadmap-card h3 {font-size:17px;font-weight:700;margin:8px 0 10px;color:#203b60;}
.roadmap-card p {font-size:13px;line-height:1.8;color:#64758d;margin:0;}
@media(max-width:900px){.roadmap-grid{grid-template-columns:1fr;}}
@media(max-width:700px){.block-container{padding-left:1rem;padding-right:1rem;}.metric-row{gap:6px}.metric-card{padding:10px}.metric-card strong{font-size:20px}.metric-card span{display:none}}
</style>
"""


def graph_svg(graph, frame, source, target=None, show_costs=True):
    path = path_to(frame.parents, source, target) if target in frame.settled else []
    selected_edges = {frozenset((u, v)) for u, v in zip(path, path[1:])}
    tree_edges = {frozenset((v, p)) for v, p in frame.parents.items() if p is not None}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 530" role="img" aria-label="현재 다익스트라 알고리즘의 그래프 상태" style="width:100%;height:auto;display:block">',
             '<defs><pattern id="dots" x="0" y="0" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#27364c"/></pattern></defs>',
             '<rect width="720" height="530" fill="url(#dots)"/>']
    # 강조 간선을 마지막에 그려 교차점에서도 현재 검사 간선이 보이게 합니다.
    def priority(edge):
        key = frozenset(edge[:2])
        return 3 if frame.edge and key == frozenset(frame.edge) else 2 if key in selected_edges else 1 if key in tree_edges else 0

    for u, v, cost in sorted(graph.edges, key=priority):
        x1, y1 = graph.positions[u]
        x2, y2 = graph.positions[v]
        key = frozenset((u, v))
        active = frame.edge is not None and key == frozenset(frame.edge)
        color, width, dash = "#42516b", 2, ""
        if key in tree_edges:
            final_edge = u in frame.settled and v in frame.settled
            color, width = ("#5a9bff", 4) if final_edge else ("#6286b5", 2.8)
            dash = '' if final_edge else 'stroke-dasharray="7 5"'
        if key in selected_edges:
            color, width, dash = "#c5a0ff", 6, ""
        if active:
            color = "#4ed8af" if frame.kind == "relax" else "#ffc76b"
            width, dash = 5, ""
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}" {dash} stroke-linecap="round"><title>{u} — {v}: 비용 {cost}</title></line>')
    if show_costs:
        occupied = []
        for u, v, cost in graph.edges:
            x1, y1 = graph.positions[u]
            x2, y2 = graph.positions[v]
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            options = []
            for t in [0.5, 0.38, 0.62, 0.28, 0.72]:
                for offset in [0, 16, -16, 28, -28]:
                    x, y = x1 + dx * t - dy / length * offset, y1 + dy * t + dx / length * offset
                    penalty = sum(max(0, 37 - math.hypot(x - a, y - b)) ** 2 for a, b in occupied)
                    penalty += sum(max(0, 45 - math.hypot(x - a, y - b)) ** 2 * 3 for a, b in graph.positions.values())
                    penalty += abs(offset) * 0.2 + abs(t - 0.5) * 5
                    options.append((penalty, x, y))
            _, x, y = min(options)
            occupied.append((x, y))
            active = frame.edge and frozenset((u, v)) == frozenset(frame.edge)
            text_color = "#ffe0a8" if active else "#d1dded"
            parts.append(f'<rect x="{x-14:.1f}" y="{y-10:.1f}" width="28" height="20" rx="6" fill="#172840" stroke="#394b65"/><text x="{x:.1f}" y="{y+4:.1f}" fill="{text_color}" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="600">{cost}</text>')
    for node in graph.nodes:
        x, y = graph.positions[node]
        fill, stroke, text = "#192c46", "#7085a3", "#e4edfa"
        if node in frame.settled:
            fill, stroke = "#204d79", "#70adff"
        if node in path:
            fill, stroke = "#49366b", "#d1acff"
        if node == frame.changed:
            fill, stroke = "#145f52", "#4ed8af"
        if node == frame.current:
            fill, stroke, text = "#795522", "#ffc76b", "#fff2d9"
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="31" fill="none" stroke="#ffc76b" stroke-opacity=".28" stroke-width="7"/>')
        if node == source:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="29" fill="none" stroke="#5a9bff" stroke-width="2"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="23" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/><text x="{x:.1f}" y="{y+6:.1f}" text-anchor="middle" font-family="sans-serif" font-size="19" font-weight="700" fill="{text}">{node}</text>')
        label = f'd={number(frame.distances[node])}'
        parts.append(f'<rect x="{x-24:.1f}" y="{y+31:.1f}" width="48" height="20" rx="6" fill="#101e34"/><text x="{x:.1f}" y="{y+45:.1f}" text-anchor="middle" fill="{stroke}" font-family="sans-serif" font-size="12">{label}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def set_step(index):
    st.session_state.step = max(0, min(index, len(st.session_state.frames) - 1))
    st.session_state.playing = False


def toggle_play():
    state = st.session_state
    if state.step == len(state.frames) - 1:
        state.step = 0
    state.playing = not state.playing
    state.last_tick = time.monotonic()


def randomize_seed():
    previous = st.session_state.graph_seed
    new = secrets.randbelow(1_000_000_000)
    st.session_state.graph_seed = new if new != previous else (new + 1) % 1_000_000_000


def result_rows(graph, frame, source):
    rows = []
    for node in graph.nodes:
        path = path_to(frame.parents, source, node)
        rows.append({
            "정점": node,
            "최단거리": number(frame.distances[node]) if node in frame.settled else "미확정",
            "최단경로": " → ".join(path) if node in frame.settled else "—",
            "이전 정점": frame.parents[node] or "—",
        })
    return rows


def results_csv(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def sidebar():
    state = st.session_state
    st.markdown('<div class="eyebrow">NETWORK LAB / 01</div>', unsafe_allow_html=True)
    st.header("그래프 설정")
    st.caption("그래프를 만들고, 시작점을 골라 보세요.")
    n = st.slider("정점 수", 8, 12, 10, key="node_count")
    density = st.select_slider("간선 밀도", ["간결", "보통", "촘촘"], value="보통", key="edge_density")
    low, high = st.slider("간선 비용 범위", 1, 50, (1, 20), key="cost_range")
    state.setdefault("graph_seed", 20261030)
    st.number_input("그래프 번호 (시드)", min_value=0, max_value=999_999_999, value=None, step=1, key="graph_seed")
    st.button("↻  새 랜덤 그래프", on_click=randomize_seed, width="stretch")
    if state.graph_seed is None:
        st.info("그래프 번호를 입력하거나 ‘새 랜덤 그래프’를 눌러주세요.")
        st.stop()
    st.caption("같은 설정과 그래프 번호로 다시 만들 수 있습니다. 설정 변경 시 진행 과정은 초기화됩니다.")
    config = (n, density, low, high, state.graph_seed)
    if state.get("graph_config") != config:
        state.graph = generate_graph(*config)
        state.graph_config = config
        state.playing = False
        state.step = 0
    graph = state.graph
    if state.get("source_node") not in graph.nodes:
        state.source_node = graph.nodes[0]
    if state.get("target_node") not in ("전체 트리", *graph.nodes):
        state.target_node = "전체 트리"
    st.divider()
    st.markdown("**탐색 설정**")
    source = st.selectbox("시작 정점", graph.nodes, key="source_node")
    speed = st.select_slider("자동 재생 간격", [0.25, 0.5, 0.8, 1.2, 2.0], value=0.8, format_func=lambda v: f"{v:g}초 / 단계", key="play_interval")
    costs = st.checkbox("간선 비용 표시", value=True, key="show_costs")
    st.divider()
    st.caption("무방향 · 연결 그래프 · 양의 정수 비용")
    st.caption("선의 길이는 비용과 무관합니다. 간선 위 숫자가 실제 비용입니다.")
    return graph, source, speed, costs


def render_state_table(graph, frame):
    rows = []
    for node in graph.nodes:
        cls = "changed" if node == frame.changed else "active" if node == frame.current else ""
        settled = node in frame.settled
        status = '<span class="done">✓ 확정</span>' if settled else '<span class="pending">미확정</span>'
        rows.append(f'<tr class="{cls}"><td><b>{node}</b></td><td><b>{number(frame.distances[node])}</b></td><td>{frame.parents[node] or "—"}</td><td>{status}</td></tr>')
    return '<div class="panel"><div class="phase">DISTANCE TABLE</div><table class="distance-table"><thead><tr><th>정점</th><th>거리 d</th><th>이전</th><th>상태</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'


def render_guide():
    """시뮬레이션 오른쪽에 항상 표시하는 이론 설명과 사용법입니다."""
    st.html('''
    <section class="panel" aria-label="이론적 배경">
      <div class="phase">THEORY / 이론적 배경</div>
      <h2 class="guide-heading">다익스트라 알고리즘</h2>
      <div class="guide-text">
        <p>하나의 <b>시작 정점</b>에서 다른 모든 정점까지 가는 <b>최소 비용 경로</b>를 구하는 알고리즘입니다. 여기서 거리는 경로를 이루는 간선 비용의 합을 뜻합니다.</p>
        <ol>
          <li><b>초기화:</b> 시작점의 거리 추정값을 0, 나머지 정점은 ∞로 둡니다.</li>
          <li><b>정점 확정:</b> 미확정 정점 중 거리 추정값이 가장 작은 정점을 선택합니다.</li>
          <li><b>간선 검사:</b> 선택한 정점을 거쳐 이웃으로 가는 비용을 계산합니다.</li>
          <li><b>거리 갱신:</b> 새로운 경로가 더 짧으면 거리와 이전 정점을 바꿉니다.</li>
          <li>모든 정점이 확정될 때까지 2~4를 반복합니다.</li>
        </ol>
      </div>
      <div class="formula">d(v) ← min{ d(v), d(u) + cost(u, v) }</div>
      <div class="guide-note"><b>왜 확정할 수 있나요?</b><br>미확정 정점 중 최소 거리 정점을 고르면, 다른 미확정 정점을 거치는 우회 경로도 이 값보다 작아질 수 없습니다. 간선 비용이 모두 비음수이기 때문입니다.</div>
      <div class="guide-text" style="margin-top:12px"><p><b>적용 조건:</b> 음수 비용이 없어야 합니다. 이 앱은 양의 정수 비용만 사용합니다.</p><p><b>이전 정점:</b> 현재 경로에서 바로 앞에 있는 정점입니다. 이 정보를 거꾸로 따라가면 경로를 복원할 수 있습니다.</p></div>
    </section>
    <section class="panel" aria-label="자세한 사용 방법">
      <div class="phase">HOW TO USE / 사용 방법</div>
      <h2 class="guide-heading">직접 실험해 보세요</h2>
      <div class="guide-text">
        <ol>
          <li><b>그래프 설정:</b> 왼쪽 사이드바에서 정점 수(8~12개), 간선 밀도, 비용 범위를 선택합니다. 사이드바가 접혀 있으면 왼쪽 위 펼치기 버튼을 누릅니다.</li>
          <li><b>새 그래프 생성:</b> ‘새 랜덤 그래프’를 누릅니다. 같은 설정과 그래프 번호(시드)를 사용하면 같은 그래프를 다시 만들 수 있습니다.</li>
          <li><b>시작점 선택:</b> ‘시작 정점’ 목록에서 원하는 정점을 고릅니다. 시작점을 바꾸면 탐색은 처음부터 다시 시작합니다.</li>
          <li><b>단계별 실행:</b> ‘다음 →’을 눌러 정점 확정, 간선 검사, 거리 갱신·유지를 차례로 확인합니다. ‘← 이전’으로 돌아갈 수 있습니다.</li>
          <li><b>자동 실행:</b> ‘▶ 자동 재생’을 누릅니다. ‘Ⅱ 일시정지’로 멈추고, 사이드바에서 단계 간격을 조절할 수 있습니다.</li>
          <li><b>변화 관찰:</b> 현재 단계의 설명·계산식과 그래프 색, 거리표를 함께 보세요. 정점 아래의 d는 현재 거리 추정값입니다.</li>
          <li><b>최종 결과:</b> 계산이 끝나면 모든 최단거리와 경로가 표로 표시됩니다. ‘최종 결과 ≫’으로 곧바로 이동할 수도 있습니다.</li>
          <li><b>개별 경로 확인:</b> ‘경로 강조’에서 도착점을 고르면 확정된 최단경로가 보라색으로 표시됩니다. ‘전체 트리’를 고르면 모든 경로의 트리를 봅니다.</li>
        </ol>
      </div>
      <div class="guide-note"><b>읽을 때 주의하세요</b><br>• 선의 길이가 아니라 간선에 적힌 숫자가 비용입니다.<br>• 미확정 정점의 거리 추정값은 나중에 줄어들 수 있습니다.<br>• 최소 비용 경로가 여러 개이면 그중 하나를 표시합니다.<br>• 그래프 설정을 바꾸면 진행 과정이 초기화됩니다.</div>
    </section>
    ''')
    with st.expander("의사코드와 시간복잡도"):
        st.code('''d[source] = 0; d[other] = infinity
while unvisited:
    u = minimum_distance_vertex(unvisited)
    settle(u)
    for v in unvisited_neighbors(u):
        if d[u] + cost(u, v) < d[v]:
            d[v] = d[u] + cost(u, v)
            parent[v] = u''', language="python")
        st.caption("이 구현은 정점을 선형 탐색으로 선택하므로 O(|V|² + |E|)입니다. 애니메이션용 상태 기록 비용은 별도입니다.")


def render_roadmap():
    """현재 구현과 구별하여 향후 확장 방향만 소개합니다."""
    st.markdown("## 앞으로의 확장 계획")
    st.caption("현재 구현 범위는 다익스트라 시뮬레이션입니다. 아래 항목은 아직 구현하지 않은 향후 계획입니다.")
    st.html('''
    <div class="roadmap-grid">
      <article class="roadmap-card"><div class="number">PLAN 01</div><h3>내가 만드는 네트워크</h3><p>정점·간선을 직접 추가하거나 비용을 수정하고, 파일에서 그래프를 불러올 수 있도록 확장할 계획입니다.</p></article>
      <article class="roadmap-card"><div class="number">PLAN 02</div><h3>최단경로 알고리즘 비교</h3><p>벨만–포드와 플로이드–워셜을 추가하여 음수 간선 처리, 탐색 과정, 적용 범위의 차이를 비교할 계획입니다.</p></article>
      <article class="roadmap-card"><div class="number">PLAN 03</div><h3>조합최적화 실험실로 확장</h3><p>최소신장트리와 최대유량 알고리즘의 진행 과정을 추가하여 서로 다른 네트워크 최적화 문제를 학습하는 도구로 발전시킬 계획입니다.</p></article>
    </div>
    ''')


def main():
    st.set_page_config(page_title="최단경로 실험실 · Dijkstra", page_icon="🔵", layout="wide")
    st.html(CSS)
    with st.sidebar:
        graph, source, interval, show_costs = sidebar()
    state = st.session_state
    signature = (state.graph_config, source)
    if state.get("trace_signature") != signature:
        state.frames = dijkstra_frames(graph, source)
        state.trace_signature = signature
        state.step = 0
        state.playing = False
        state.last_tick = time.monotonic()

    st.markdown('<div class="eyebrow">INTERACTIVE ALGORITHM STUDIO</div><h1 class="app-title">최단경로 실험실<span style="color:#2673ec">.</span></h1><div class="subtitle">다익스트라 알고리즘 시뮬레이터 · 무작위 네트워크에서 하나의 시작점부터 모든 정점까지, 최단경로가 만들어지는 과정을 살펴보세요.</div>', unsafe_allow_html=True)

    @st.fragment(run_every=0.25)
    def player():
        now = time.monotonic()
        if state.playing and now - state.last_tick >= interval:
            state.step = min(state.step + 1, len(state.frames) - 1)
            state.last_tick = now
            if state.step == len(state.frames) - 1:
                state.playing = False
        frame = state.frames[state.step]
        final = state.step == len(state.frames) - 1
        cards = [("정점 / 간선", f"{len(graph.nodes)} / {len(graph.edges)}", "개"),
                 ("시작 정점", source, "에서 출발"),
                 ("최단거리 확정", f"{len(frame.settled)}", f"/ {len(graph.nodes)}"),
                 ("간선 검사 / 갱신", f"{frame.checks} / {frame.updates}", "회")]
        st.html('<div class="metric-row">' + ''.join(f'<div class="metric-card"><small>{label}</small><strong>{value}</strong><span>{unit}</span></div>' for label, value, unit in cards) + '</div>')

        buttons = st.columns([1.35, 1, 1, 1, 1.3])
        with buttons[0]:
            st.button("Ⅱ 일시정지" if state.playing else "▶ 자동 재생", on_click=toggle_play, type="primary", width="stretch", key="play")
        with buttons[1]:
            st.button("← 이전", on_click=set_step, args=(state.step - 1,), disabled=state.step == 0, width="stretch", key="previous")
        with buttons[2]:
            st.button("다음 →", on_click=set_step, args=(state.step + 1,), disabled=final, width="stretch", key="next")
        with buttons[3]:
            st.button("↺ 처음", on_click=set_step, args=(0,), width="stretch", key="reset")
        with buttons[4]:
            st.button("최종 결과 ≫", on_click=set_step, args=(len(state.frames) - 1,), disabled=final, width="stretch", key="finish")
        st.progress(state.step / (len(state.frames) - 1), text=f"단계 {state.step} / {len(state.frames) - 1} · {'자동 재생 중' if state.playing else '완료' if final else '직접 탐색'}")
        st.caption("한 단계 = 정점 확정 또는 간선 검사·갱신/유지. 이미 확정된 이웃은 다시 검사하지 않습니다.")

        target = st.selectbox("경로 강조 · 확정된 정점의 경로를 확인하세요", ("전체 트리", *graph.nodes), key="target_node")
        selected = None if target == "전체 트리" else target
        if selected is not None:
            if selected in frame.settled:
                path = path_to(frame.parents, source, selected)
                st.html(f'<div class="path-pill"><b>{" → ".join(path)}</b> &nbsp;·&nbsp; 최단거리 <b>{number(frame.distances[selected])}</b></div>')
            else:
                st.caption(f"{selected}는 아직 미확정입니다. 확정되는 단계부터 해당 최단경로를 강조합니다.")

        phase = {"init": "00 / INITIALIZE", "settle": "01 / SELECT & SETTLE", "inspect": "02 / CHECK EDGE", "relax": "03 / UPDATE DISTANCE", "keep": "03 / KEEP DISTANCE", "done": "04 / COMPLETE"}[frame.kind]
        formula = f'<div class="formula">{html.escape(frame.formula)}</div>' if frame.formula else ''
        st.html(f'<div class="panel"><div class="phase">{phase}</div><div class="event-title">{html.escape(frame.title)}</div><div class="event-text" style="min-height:0">{html.escape(frame.message)}</div>{formula}</div>')
        svg = graph_svg(graph, frame, source, selected, show_costs)
        legend = '<div class="legend"><span><i style="background:#ffc76b"></i>현재 정점·검사 간선</span><span><i style="background:#4ed8af"></i>거리 갱신</span><span><i style="background:#70adff"></i>확정 정점·트리</span><span><i style="background:#c5a0ff"></i>선택한 최단경로</span></div>'
        st.html(f'<div class="board"><div class="board-head">NETWORK VIEW<span>무방향 · 비용 {state.cost_range[0]}–{state.cost_range[1]} · #{graph.seed}</span></div>{svg}{legend}</div>')
        pending = sorted((node for node in graph.nodes if node not in frame.settled), key=lambda v: (frame.distances[v], v))
        queue = ''.join(f'<span>{node} : {number(frame.distances[node])}</span>' for node in pending)
        st.html('<div class="panel" style="margin-top:14px"><div class="phase">NEXT CANDIDATES</div><div style="font-size:12px;color:#6b7c93">미확정 정점을 현재 거리순으로 표시합니다. 동률이면 이름순입니다.</div><div class="queue">' + (queue or '<span>모든 정점 확정 완료</span>') + '</div></div>')
        st.html(render_state_table(graph, frame))

        if final:
            st.success(f"탐색 완료 · {source}에서 모든 정점까지의 최단경로입니다.")
            rows = result_rows(graph, frame, source)
            st.dataframe(rows, hide_index=True, width="stretch")
            st.download_button("최단경로 결과 CSV 다운로드", data=results_csv(rows), file_name=f"shortest_paths_{source}_{graph.seed}.csv", mime="text/csv", key="download_result")

        with st.expander("진행 기록 보기", expanded=False):
            for i, item in enumerate(state.frames[:state.step + 1]):
                st.markdown(f"**{i:02d} · {item.title}** — {item.message}")

    simulation, guide = st.columns([2.05, 1], gap="large")
    with simulation:
        st.markdown("### 시뮬레이션")
        player()
    with guide:
        render_guide()
    st.divider()
    render_roadmap()
    st.markdown('<div class="footnote">컴퓨팅 탐색 · 최단경로 알고리즘 시뮬레이터<br>그래프와 간선 비용은 무작위로 생성됩니다. 기본 그래프는 항상 연결되며, 간선 비용은 양의 정수입니다.</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
