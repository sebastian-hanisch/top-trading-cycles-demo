"""Plotly-Abbildungen: Karte (Zielpunkte, Plätze, aktuelle Zeiger und abgeschlossene Tausche), Kreislängen-Histogramm,
Längenbeschränkungs-Vorschau, Aufwand gegen Größe. Achsen gesperrt (fixedrange) für Touch-Geräte."""

import plotly.graph_objects as go

import tt_constants as C
from tt_ttc import state_at

TARGET_COLOR = "#111111"
SLOT_COLOR = "#1f77b4"
POINT_COLOR = "#bbbbbb"
CYCLE_COLOR = "#2ca02c"
LAST_CYCLE_COLOR = "#9467bd"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.08), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _map_layout(fig, sc, height):
    pts = list(sc.targets) + list(sc.slots)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 8
    fig.update_xaxes(visible=False, range=[min(xs) - pad, max(xs) + pad], scaleanchor="y", scaleratio=1, constrain="domain")
    fig.update_yaxes(visible=False, range=[min(ys) - pad, max(ys) + pad], constrain="domain")
    return _base(fig, height)


def _seg(p0, p1):
    return [p0[0], p1[0], None], [p0[1], p1[1], None]


def build_map(sc, prefs, res, k, height=430):
    """Zielpunkte (Kreise) und Plätze (Quadrate); dünne graue Linie = aktueller Zeiger einer noch aktiven Person,
    dicke grüne Linie = abgeschlossener Tausch, lila = der zuletzt gefundene Kreis."""
    n = sc.n
    state = state_at(res, n, k)
    matched, left = state["matched"], state["left"]
    last_cycle = set(state["last_cycle"] or ())
    fig = go.Figure()

    px, py = [], []
    for i in range(n):
        if i in left:
            continue
        s = prefs[i][state["cursor_advance"][i]]
        x, y = _seg(sc.targets[i], sc.slots[s])
        px += x
        py += y
    if px:
        fig.add_trace(go.Scatter(x=px, y=py, mode="lines", line=dict(color=POINT_COLOR, width=1, dash="dot"), hoverinfo="skip", name="zeigt auf"))

    cx, cy, ox, oy = [], [], [], []
    for i, s in matched.items():
        x, y = _seg(sc.targets[i], sc.slots[s])
        if i in last_cycle:
            ox += x
            oy += y
        else:
            cx += x
            cy += y
    if cx:
        fig.add_trace(go.Scatter(x=cx, y=cy, mode="lines", line=dict(color=CYCLE_COLOR, width=3), hoverinfo="skip", name="getauscht"))
    if ox:
        fig.add_trace(go.Scatter(x=ox, y=oy, mode="lines", line=dict(color=LAST_CYCLE_COLOR, width=4), hoverinfo="skip", name="letzter Kreis"))

    small = n <= 30
    active_idx = [i for i in range(n) if i not in left]
    left_idx = sorted(left)
    for idx, name, symbol in ((active_idx, "aktiv", "circle-open"), (left_idx, "hat getauscht/verlässt", "circle")):
        if idx:
            fig.add_trace(go.Scatter(x=[sc.targets[i][0] for i in idx], y=[sc.targets[i][1] for i in idx], mode="markers+text" if small else "markers", name=name,
                                     text=[str(i) for i in idx] if small else None, textposition="top center", hovertext=[f"Person {i}" for i in idx], hoverinfo="text",
                                     marker=dict(symbol=symbol, size=11, color=TARGET_COLOR, line=dict(width=2, color=TARGET_COLOR))))
    fig.add_trace(go.Scatter(x=[p[0] for p in sc.slots], y=[p[1] for p in sc.slots], mode="markers+text" if small else "markers", name="Plätze",
                             text=[str(s) for s in range(n)] if small else None, textposition="bottom center", hovertext=[f"Platz {s}" for s in range(n)], hoverinfo="text",
                             marker=dict(symbol="square", size=10, color=SLOT_COLOR, line=dict(width=2, color=SLOT_COLOR))))
    fig = _map_layout(fig, sc, height)
    fig.update_layout(showlegend=False)
    return fig


def build_progress(res, k, height=220):
    xs = list(range(res.n_events + 1))
    left_count, cur = [0], 0
    for e in res.events:
        if e.kind == "cycle":
            cur += len(e.cycle)
        left_count.append(cur)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=left_count, mode="lines", name="haben getauscht/verlassen", line=dict(color=CYCLE_COLOR, shape="hv")))
    fig.add_vline(x=k, line=dict(color="#333", width=2))
    fig.update_xaxes(title="Ereignis")
    fig.update_yaxes(title="Personen fertig", rangemode="tozero")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.45))
    return fig


def build_length_hist(hist_share, height=280):
    lengths = sorted(hist_share)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(L) for L in lengths], y=[100 * hist_share[L] for L in lengths], marker_color=CYCLE_COLOR))
    fig.update_xaxes(title="Kreislänge")
    fig.update_yaxes(title="Anteil aller Kreise [%]", rangemode="tozero")
    return _base(fig, height)


def build_cap_preview(rows, height=280):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[f"≤ {r['cap']}" for r in rows], y=[100 * r["lost_dist_share"] for r in rows], name="verlorener Distanzgewinn [%]", marker_color="#d62728"))
    fig.add_trace(go.Bar(x=[f"≤ {r['cap']}" for r in rows], y=[100 * r["lost_rank_share"] for r in rows], name="verlorener Rang-Gewinn [%]", marker_color="#ff7f0e"))
    fig.update_xaxes(title="Höchstlänge zugelassener Kreise")
    fig.update_yaxes(title="Verlorener Gewinn [%]", rangemode="tozero", range=[0, 105])
    fig.update_layout(barmode="group")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 30)
    return fig


def build_scale(rows, worst_rows, height=320):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["n"] for r in rows], y=[r["steps"] for r in rows], mode="lines+markers", name="Aufwand (geometrische Karte)", line=dict(color=SLOT_COLOR)))
    fig.add_trace(go.Scatter(x=[r["n"] for r in worst_rows], y=[r["steps"] for r in worst_rows], mode="lines+markers", name="Aufwand (Worst Case)", line=dict(color="#d62728")))
    fig.add_trace(go.Scatter(x=[r["n"] for r in worst_rows], y=[r["n"] ** 2 for r in worst_rows], mode="lines", name="n²", line=dict(color="#888", dash="dot")))
    fig.update_xaxes(title="n", type="log")
    fig.update_yaxes(title="Schritte (Listenvorrücken + Verfolgungsschritte)", type="log")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 40)
    return fig
