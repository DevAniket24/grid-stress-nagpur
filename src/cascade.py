"""Cascade model power -> water -> hospitals on a NetworkX dependency graph (notebooks 04 and 05)."""
import numpy as np
# ---- Cascade model: power -> water -> hospitals (shared by notebooks 04 and 05) ----
import networkx as nx


def build_dependency_graph(fac):
    """Directed dependency graph. Edge u -> v means 'v needs u'.
    bus -> pump (power), bus -> hospital (power), pump -> hospital (water), pump -> water zone (water)."""
    G = nx.DiGraph()
    for b in sorted(fac.bus.unique()):
        G.add_node(f"bus{b}", kind="bus", bus=int(b), layer=0)
    for _, f in fac[fac.type == "pump"].iterrows():
        G.add_node(f["id"], kind="pump", layer=1)
        G.add_edge(f"bus{f['bus']}", f["id"], dep="power")
        G.add_node(f"zone_{f['id']}", kind="water_zone", pop=float(f["pop"]), layer=2)
        G.add_edge(f["id"], f"zone_{f['id']}", dep="water")
    for _, f in fac[fac.type == "hospital"].iterrows():
        G.add_node(f["id"], kind="hospital", tier=f["tier"], beds=float(f["beds"]), layer=2)
        G.add_edge(f"bus{f['bus']}", f["id"], dep="power")
        G.add_edge(f["pump"], f["id"], dep="water")
    assert nx.is_directed_acyclic_graph(G)
    return G


def dependency_arrays(G):
    """Turn the graph into index arrays, processed layer by layer (topological generations)."""
    nodes = {k: [n for n, d in G.nodes(data=True) if d["kind"] == k] for k in ["bus", "pump", "hospital", "water_zone"]}
    pos = {k: {n: i for i, n in enumerate(v)} for k, v in nodes.items()}
    def pred(n, kind):
        return next(u for u in G.predecessors(n) if G.nodes[u]["kind"] == kind)
    arr = dict(
        nodes=nodes,
        bus_ids=np.array([G.nodes[n]["bus"] for n in nodes["bus"]]),
        pump_bus=np.array([pos["bus"][pred(p, "bus")] for p in nodes["pump"]]),
        hosp_bus=np.array([pos["bus"][pred(h, "bus")] for h in nodes["hospital"]]),
        hosp_pump=np.array([pos["pump"][pred(h, "pump")] for h in nodes["hospital"]]),
        zone_pump=np.array([pos["pump"][pred(z, "pump")] for z in nodes["water_zone"]]),
        zone_pop=np.array([G.nodes[z]["pop"] for z in nodes["water_zone"]]),
        hosp_beds=np.array([G.nodes[h]["beds"] for h in nodes["hospital"]]),
        hosp_tier=np.array([G.nodes[h]["tier"] for h in nodes["hospital"]]),
        generations=[sorted({G.nodes[n]["kind"] for n in g}) for g in nx.topological_generations(G)],
    )
    return arr


def shed_fraction_matrix(ts_scenario, bus_ids, bus_load, horizon):
    """Hourly fraction of each bus's load that is shed (T x n_bus)."""
    F = np.zeros((horizon, len(bus_ids)))
    if len(ts_scenario):
        piv = ts_scenario.pivot_table(index="hour", columns="bus", values="shed_mw", aggfunc="sum")
        piv = piv.reindex(index=range(horizon), columns=bus_ids).fillna(0.0)
        F = np.clip(piv.values / np.maximum(bus_load.reindex(bus_ids).values, 1e-9), 0, 1)
    return F


def _battery_step(on_grid, soc, cap, pv_kw, load_kw, charge_rate):
    """One hour of PV + battery. Returns (supplied, new_soc). Grid-connected: battery recharges."""
    surplus = pv_kw - load_kw
    soc_off = soc + np.where(surplus >= 0, np.minimum(surplus, cap - soc), surplus)
    ok_off = soc_off >= -1e-9
    soc_off = np.clip(soc_off, 0, cap)
    soc_on = np.minimum(cap, soc + charge_rate * cap)
    return np.where(on_grid, True, ok_off), np.where(on_grid, soc_on, soc_off)


def cascade_simulate(A, F, P, backup=None):
    """Hourly simulation of facility states for one scenario.

    A: dependency arrays; F: shed fraction (T x n_bus); P: parameters;
    backup: optional {"hospital"|"pump": dict(pv_kwp, batt_kwh, load_kw (T x n), pv (T,))}.
    Returns per-facility hourly states."""
    T = F.shape[0]
    npump, nh = len(A["pump_bus"]), len(A["hosp_bus"])
    pump_grid = F[:, A["pump_bus"]] < P["PUMP_SHED_THRESHOLD"]
    hosp_grid = F[:, A["hosp_bus"]] < P["HOSP_SHED_THRESHOLD"]

    def run_backup(kind, grid):
        if not backup or kind not in backup:
            return np.zeros_like(grid)
        b = backup[kind]
        cap = b["batt_kwh"].astype(float)
        soc = cap * P.get("SOC_START", 1.0)
        sup = np.zeros_like(grid)
        for t in range(T):
            pvk = b["pv_kwp"] * b["pv"][t]
            s, soc = _battery_step(grid[t], soc, cap, pvk, b["load_kw"][t], P.get("CHARGE_RATE", 0.5))
            sup[t] = s & ~grid[t]
        return sup

    pump_backup = run_backup("pump", pump_grid)
    pfuel = np.full(npump, float(P.get("PUMP_DG_H", 0)))

    # water network storage (elevated service reservoirs), hours of demand
    S = np.full(npump, float(P["WATER_STORAGE_H"]))
    pump_on = np.zeros((T, npump), bool)
    zone_water = np.zeros((T, npump), bool)
    for t in range(T):
        g = pump_grid[t] | pump_backup[t]
        dg = ~g & (pfuel > 0)
        pfuel = np.where(dg, pfuel - 1, pfuel)
        on = g | dg
        pump_on[t] = on
        zone_water[t] = on | (S > 0)
        S = np.where(on, np.minimum(P["WATER_STORAGE_H"], S + P["REFILL_PER_H"]), np.maximum(S - 1, 0))

    hosp_backup = run_backup("hospital", hosp_grid)
    fuel = np.where(A["hosp_tier"] == "major", P["DG_HOURS_MAJOR"], P["DG_HOURS_SMALL"]).astype(float)
    W = np.full(nh, float(P["HOSP_WATER_H"]))
    hp, hw = np.zeros((T, nh), bool), np.zeros((T, nh), bool)
    for t in range(T):
        g = hosp_grid[t] | hosp_backup[t]
        dg = ~g & (fuel > 0)
        fuel = np.where(dg, fuel - 1, fuel)
        hp[t] = g | dg
        zw = zone_water[t, A["hosp_pump"]]
        hw[t] = zw | (W > 0)
        W = np.where(zw, np.minimum(P["HOSP_WATER_H"], W + P["REFILL_PER_H"]), np.maximum(W - 1, 0))
    return dict(pump_grid=pump_grid, pump_on=pump_on, zone_water=zone_water,
                hosp_grid=hosp_grid, hosp_power=hp, hosp_water=hw, hosp_ok=hp & hw)


def cascade_metrics(A, R):
    down = ~R["hosp_ok"]
    power_down = ~R["hosp_power"]
    water_only = down & ~power_down
    zone_down = ~R["zone_water"]
    return dict(
        hospitals_grid_off=int((~R["hosp_grid"]).any(0).sum()),
        hospitals_affected=int(down.any(0).sum()),
        hospital_hours_lost=float(down.sum()),
        hospital_hours_power=float((down & power_down).sum()),
        hospital_hours_water=float(water_only.sum()),
        bed_hours_lost=float((down * A["hosp_beds"]).sum()),
        pumps_grid_off=int((~R["pump_grid"]).any(0).sum()),
        water_zone_hours_lost=float(zone_down.sum()),
        person_hours_without_water=float((zone_down * A["zone_pop"][None, :]).sum()),
        critical_service_hours_lost=float(down.sum() + zone_down.sum()),
    )
