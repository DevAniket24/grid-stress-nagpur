"""Storm-corridor hazard model: wind footprint, tower fragility, crew-limited restoration (notebook 01)."""
import numpy as np
# ---- Storm-corridor hazard model (notebook 01) ----
import json
import numpy as np
import pandas as pd
from scipy.stats import norm


def bus_coordinates(net, box_km=250.0, centre=(21.15, 79.09)):
    """Place the (non-geographic) test network in a box_km x box_km square centred on the site.
    Uses pandapower's generic bus coordinates; the placement is synthetic and only gives the
    hazard footprint a spatial meaning."""
    xy = np.array([json.loads(g)["coordinates"] for g in net.bus.geo])
    xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0)).max()              # keep aspect ratio
    xy = (xy - xy.max(0) / 2) * box_km                                  # km, centred on 0,0
    lat0, lon0 = centre
    df = pd.DataFrame({"x_km": xy[:, 0], "y_km": xy[:, 1]}, index=net.bus.index)
    df["lat"] = lat0 + df.y_km / 110.574
    df["lon"] = lon0 + df.x_km / (111.320 * np.cos(np.radians(lat0)))
    return df


def line_geometry(net, coords):
    f = coords.loc[net.line.from_bus].values[:, :2]
    t = coords.loc[net.line.to_bus].values[:, :2]
    g = pd.DataFrame({"x0": f[:, 0], "y0": f[:, 1], "x1": t[:, 0], "y1": t[:, 1]}, index=net.line.index)
    g["length_km"] = np.hypot(g.x1 - g.x0, g.y1 - g.y0).clip(lower=1.0)
    return g


def dist_to_segment(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    tt = np.clip(((px - ax) * abx + (py - ay) * aby) / max(abx ** 2 + aby ** 2, 1e-12), 0, 1)
    return np.hypot(px - (ax + tt * abx), py - (ay + tt * aby))


def corridor_endpoints(offset_km, bearing_deg, length_km):
    """Straight storm track crossing the box. bearing = direction of travel (0 = north, 90 = east);
    offset = perpendicular shift of the track from the box centre."""
    th = np.radians(bearing_deg)
    d = np.array([np.sin(th), np.cos(th)])          # unit vector of travel (x = east, y = north)
    nrm = np.array([d[1], -d[0]])
    c = nrm * offset_km
    return c - d * length_km / 2, c + d * length_km / 2


def gust_field(px, py, track, v_peak, sigma_km, v_background=0.0):
    """Peak gust (m/s) at points: Gaussian decay with distance from the storm track."""
    (ax, ay), (bx, by) = track
    d = dist_to_segment(px, py, ax, ay, bx, by)
    return v_background + (v_peak - v_background) * np.exp(-0.5 * (d / sigma_km) ** 2)


def tower_fragility(v, median=65.0, beta=0.12):
    """Probability that one tower/span fails at gust v (lognormal fragility curve)."""
    v = np.maximum(np.asarray(v, float), 1e-6)
    return norm.cdf(np.log(v / median) / beta)


def line_failure_prob(geom, track, v_peak, sigma_km, span_km=0.35, median=65.0, beta=0.12):
    """Each line is a chain of towers; it fails if any tower fails: P = 1 - prod(1 - p_tower)."""
    p, vmax = [], []
    for _, g in geom.iterrows():
        n = max(int(np.ceil(g.length_km / span_km)), 1)
        s = (np.arange(n) + 0.5) / n
        x = g.x0 + s * (g.x1 - g.x0); y = g.y0 + s * (g.y1 - g.y0)
        v = gust_field(x, y, track, v_peak, sigma_km)
        pt = tower_fragility(v, median, beta)
        p.append(1 - np.exp(np.sum(np.log1p(-np.minimum(pt, 1 - 1e-12)))))
        vmax.append(v.max())
    return pd.DataFrame({"p_fail": p, "v_max": vmax}, index=geom.index)


def restoration_curve(dc, failed, n_crews=3, repair_h=24.0, delay_h=6.0, horizon_h=None):
    """Greedy restoration: after an assessment delay, each crew repairs one line every repair_h hours;
    the next line repaired is the one that reduces load shed the most.
    Returns hourly shed per bus (DataFrame hours x buses) and the repair order."""
    remaining = list(failed)
    events = []                                   # (time_h, list of outages still active)
    t = delay_h
    current = dc.solve(remaining)
    timeline = [(0.0, current["shed_bus"])]
    order = []
    while remaining:
        batch = []
        for _ in range(min(n_crews, len(remaining))):
            best, best_shed, best_res = None, np.inf, None
            for o in remaining:
                trial = [x for x in remaining if x != o]
                r = dc.solve(trial)
                s = r["shed_mw"] if r["ok"] else np.inf
                if s < best_shed - 1e-6:
                    best, best_shed, best_res = o, s, r
            if best is None:                          # no single repair helps: take the first
                best = remaining[0]; best_res = dc.solve(remaining[1:])
            remaining.remove(best); batch.append(best)
            current = best_res
        t += repair_h
        order.append((t, batch))
        timeline.append((t, current["shed_bus"]))
    end = int(np.ceil(timeline[-1][0])) if horizon_h is None else horizon_h
    hours = np.arange(end + 1)
    rows = []
    for h in hours:
        sb = [s for (tt, s) in timeline if tt <= h][-1]
        rows.append(sb.values)
    shed = pd.DataFrame(rows, index=hours, columns=timeline[0][1].index)
    return shed, order
