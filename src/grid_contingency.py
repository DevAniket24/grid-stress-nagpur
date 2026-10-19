"""Grid functions: rating assignment, DC load-shed OPF, AC contingency screening (used in notebooks 01 and 03)."""
# ---- Core grid functions (shared by notebooks 01 and 03) ----
import copy
import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.topology as top
import scipy.sparse as sp
from scipy.optimize import linprog

SQRT3 = np.sqrt(3.0)


def branch_flows_mva(net):
    """Apparent power through each line and transformer (max of both ends), MVA."""
    rl = net.res_line
    s_line = np.maximum(np.hypot(rl.p_from_mw, rl.q_from_mvar), np.hypot(rl.p_to_mw, rl.q_to_mvar))
    if len(net.trafo):
        rt = net.res_trafo
        s_tr = np.maximum(np.hypot(rt.p_hv_mw, rt.q_hv_mvar), np.hypot(rt.p_lv_mw, rt.q_lv_mvar))
    else:
        s_tr = pd.Series(dtype=float)
    return s_line, s_tr


def assign_ratings(net, mode="base_flow", target_loading=0.7, floor_mva=None):
    """Give the test network realistic thermal ratings.

    mode="case": keep the ratings that come with the test case.
    mode="base_flow": rating = max(|S_base| / target_loading, voltage-level floor).
      This makes the base case secure (every branch <= target_loading) while leaving
      limited headroom, a common way to rate IEEE cases that ship without limits.
    Transformer impedances are kept constant when their MVA rating is changed.
    """
    if mode == "case":
        return net
    floor_mva = floor_mva or {}
    pp.runpp(net)
    s_line, s_tr = branch_flows_mva(net)
    vn_line = net.bus.loc[net.line.from_bus, "vn_kv"].values
    floor_l = np.array([floor_mva.get(v, 0.0) for v in vn_line])
    rating_l = np.maximum(s_line.values / target_loading, floor_l)
    rating_l = np.ceil(rating_l / 5) * 5                                 # round up to 5 MVA steps
    net.line["max_i_ka"] = rating_l / (SQRT3 * vn_line * net.line.parallel.values)
    if len(net.trafo):
        vn_tr = net.bus.loc[net.trafo.hv_bus, "vn_kv"].values
        floor_t = np.array([floor_mva.get(v, 0.0) for v in vn_tr])
        rating_t = np.ceil(np.maximum(s_tr.values / target_loading, floor_t) / 5) * 5
        k = rating_t / net.trafo.sn_mva.values                           # keep ohmic impedance unchanged
        net.trafo["vk_percent"] *= k
        net.trafo["vkr_percent"] *= k
        net.trafo["sn_mva"] = rating_t
    pp.runpp(net)
    return net


def branch_table(net):
    """All lines and transformers with DC-model reactance (p.u. on net.sn_mva) and MVA rating."""
    base = net.sn_mva
    L = net.line
    vn = net.bus.loc[L.from_bus, "vn_kv"].values
    zb = vn ** 2 / base
    lines = pd.DataFrame({
        "kind": "line", "idx": L.index.values,
        "f": L.from_bus.values, "t": L.to_bus.values,
        "x_pu": L.x_ohm_per_km.values * L.length_km.values / L.parallel.values / zb,
        "rating_mva": SQRT3 * vn * L.max_i_ka.values * L.parallel.values * L.df.values,
        "in_service": L.in_service.values,
    })
    tabs = [lines]
    if len(net.trafo):
        T = net.trafo
        vk = np.sqrt(np.maximum(T.vk_percent.values ** 2 - T.vkr_percent.values ** 2, 1e-9)) / 100
        tabs.append(pd.DataFrame({
            "kind": "trafo", "idx": T.index.values,
            "f": T.hv_bus.values, "t": T.lv_bus.values,
            "x_pu": vk * base / T.sn_mva.values / T.parallel.values,
            "rating_mva": T.sn_mva.values * T.parallel.values,
            "in_service": T.in_service.values,
        }))
    bt = pd.concat(tabs, ignore_index=True)
    bt["name"] = bt["kind"].str[0].str.upper() + bt["idx"].astype(str) + " (" + bt["f"].astype(str) + "-" + bt["t"].astype(str) + ")"
    return bt


def bus_loads(net):
    """Net active demand per bus (loads minus static generators), MW."""
    d = net.load[net.load.in_service].groupby("bus")["p_mw"].sum() if len(net.load) else pd.Series(dtype=float)
    if len(net.sgen):
        d = d.sub(net.sgen[net.sgen.in_service].groupby("bus")["p_mw"].sum(), fill_value=0)
    return d.reindex(net.bus.index, fill_value=0.0)


def generator_table(net):
    g = net.gen[net.gen.in_service]
    e = net.ext_grid[net.ext_grid.in_service]
    cost = {}
    if len(net.poly_cost):
        for _, r in net.poly_cost.iterrows():
            cost[(r.et, r.element)] = r.cp1_eur_per_mw
    gens = pd.DataFrame({
        "et": ["gen"] * len(g) + ["ext_grid"] * len(e),
        "element": list(g.index) + list(e.index),
        "bus": list(g.bus) + list(e.bus),
        "p0": list(g.p_mw) + [np.nan] * len(e),
        "pmax": list(g.max_p_mw) + list(e.max_p_mw if "max_p_mw" in e else [1e4] * len(e)),
    })
    gens["pmax"] = gens["pmax"].fillna(1e4)
    gens["cost"] = [cost.get((a, b), 20.0) for a, b in zip(gens.et, gens.element)]
    return gens


class DCLoadShed:
    """DC optimal power flow that treats every load as sheddable.

    minimise   VOLL * sum(shed) + sum(c_g * P_g)
    subject to B*theta = Cg*P_g - (P_d - shed)      (nodal balance, per unit)
               |b_l (theta_f - theta_t)| <= rating_l   (thermal limits)
               0 <= P_g <= P_g,max ; 0 <= shed <= P_d
               theta = 0 at one bus in every island
    Islands with no generation are forced to shed all their load.
    """

    def __init__(self, net, voll=10000.0, redispatch_frac=None, rating_scale=None):
        self.net = net
        self.base = net.sn_mva
        self.bt = branch_table(net)
        if rating_scale is not None:                      # e.g. heat derating of lines only
            self.bt.loc[self.bt.kind == "line", "rating_mva"] *= rating_scale
        self.buses = net.bus.index[net.bus.in_service].values
        self.pos = {b: i for i, b in enumerate(self.buses)}
        self.pd = bus_loads(net).reindex(self.buses).clip(lower=0).values
        self.gens = generator_table(net)
        self.voll = voll
        self.redispatch_frac = redispatch_frac
        self.key = {(k, i): n for n, (k, i) in enumerate(zip(self.bt.kind, self.bt.idx))}

    def solve(self, outages=(), return_flows=False):
        bt = self.bt
        on = bt.in_service.values.copy()
        for o in outages:
            on[self.key[o]] = False
        br = bt[on]
        n, m, ng = len(self.buses), len(br), len(self.gens)
        f = np.array([self.pos[b] for b in br.f]); t = np.array([self.pos[b] for b in br.t])
        b = 1.0 / br.x_pu.values
        C = sp.csr_matrix((np.r_[np.ones(m), -np.ones(m)], (np.r_[np.arange(m), np.arange(m)], np.r_[f, t])), shape=(m, n))
        Bf = sp.diags(b) @ C                                   # branch flow = Bf @ theta  (p.u.)
        Bbus = C.T @ Bf
        gb = np.array([self.pos[x] for x in self.gens.bus])
        Cg = sp.csr_matrix((np.ones(ng), (gb, np.arange(ng))), shape=(n, ng))
        # islands -> one reference angle each
        import networkx as nx
        G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(zip(f, t))
        islands = list(nx.connected_components(G))
        refs = [min(c) for c in islands]
        # variables: theta (n) | Pg (ng) | shed (n)
        nv = n + ng + n
        A_eq = sp.hstack([Bbus, -Cg, -sp.eye(n)]).tocsr()
        b_eq = -self.pd / self.base
        R = sp.csr_matrix((np.ones(len(refs)), (np.arange(len(refs)), refs)), shape=(len(refs), nv))
        A_eq = sp.vstack([A_eq, R]).tocsr(); b_eq = np.r_[b_eq, np.zeros(len(refs))]
        rate = br.rating_mva.values / self.base
        A_ub = sp.vstack([sp.hstack([Bf, sp.csr_matrix((m, ng + n))]),
                          sp.hstack([-Bf, sp.csr_matrix((m, ng + n))])]).tocsr()
        b_ub = np.r_[rate, rate]
        pmax = self.gens.pmax.values.copy()
        if self.redispatch_frac is not None:                  # limited corrective re-dispatch
            p0 = self.gens.p0.values
            up = np.where(np.isnan(p0), pmax, np.minimum(pmax, p0 + self.redispatch_frac * pmax))
            pmax = up
        bounds = [(None, None)] * n + [(0, p / self.base) for p in pmax] + [(0, d / self.base) for d in self.pd]
        cost = np.r_[np.zeros(n), self.gens.cost.values / 1000.0, np.full(n, self.voll / 1000.0)]
        res = linprog(cost, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
        if res.status != 0:
            return dict(ok=False, shed_mw=np.nan, shed_bus=None, n_islands=len(islands))
        x = res.x
        shed = x[n + ng:] * self.base
        out = dict(ok=True, shed_mw=float(shed.sum()), shed_bus=pd.Series(shed, index=self.buses),
                   n_islands=len(islands), pg=x[n:n + ng] * self.base)
        if return_flows:
            out["flows"] = pd.Series(Bf @ x[:n] * self.base, index=br.index)
        return out


def set_status(net, outages, status):
    for kind, idx in outages:
        net[kind].at[idx, "in_service"] = status


def ac_contingency(net, outages, pi_n=1):
    """AC power flow with the given (kind, idx) elements out of service. Restores the network afterwards."""
    set_status(net, outages, False)
    r = dict(converged=False)
    try:
        unsup = top.unsupplied_buses(net)
        r["n_isolated_buses"] = len(unsup)
        r["ac_load_isolated_mw"] = float(net.load[net.load.bus.isin(unsup) & net.load.in_service].p_mw.sum())
        try:
            pp.runpp(net, init="dc")
        except pp.LoadflowNotConverged:
            pp.runpp(net, init="flat", max_iteration=50)
        r["converged"] = True
        ll = net.res_line.loading_percent.where(net.line.in_service).dropna()
        tl = net.res_trafo.loading_percent.where(net.trafo.in_service).dropna() if len(net.trafo) else pd.Series(dtype=float)
        load = pd.concat([ll, tl])
        r["max_loading_pct"] = float(load.max())
        r["n_overloads"] = int((load > 100).sum())
        r["overload_excess_pct"] = float((load - 100).clip(lower=0).sum())
        r["overloaded"] = ";".join([f"L{i}" for i in ll[ll > 100].index] + [f"T{i}" for i in tl[tl > 100].index])
        r["PI"] = float(((load / 100) ** (2 * pi_n)).sum() / (2 * pi_n))       # Ejebe & Wollenberg (1979)
        vm = net.res_bus.vm_pu.dropna()
        vmin_lim = net.bus.loc[vm.index, "min_vm_pu"].fillna(0.95)
        vmax_lim = net.bus.loc[vm.index, "max_vm_pu"].fillna(1.05)
        r["vmin_pu"], r["vmax_pu"] = float(vm.min()), float(vm.max())
        r["n_voltage_violations"] = int(((vm < vmin_lim) | (vm > vmax_lim)).sum())
    except pp.LoadflowNotConverged:
        pass
    finally:
        set_status(net, outages, True)
    return r


def run_contingency_set(net, outage_list, voll=10000.0, redispatch_frac=None, rating_scale=None, label=""):
    """AC screening + DC load-shed for a list of outage sets. Returns a DataFrame."""
    dc = DCLoadShed(net, voll=voll, redispatch_frac=redispatch_frac, rating_scale=rating_scale)
    rows = []
    for outages in outage_list:
        r = ac_contingency(net, outages)
        s = dc.solve(outages)
        r.update(outage=";".join(f"{k[0].upper()}{i}" for k, i in outages), k=len(outages),
                 dc_ok=s["ok"], load_shed_mw=s["shed_mw"], n_islands=s["n_islands"])
        r["violation"] = (not r["converged"]) or r.get("n_overloads", 0) > 0 or r.get("n_voltage_violations", 0) > 0
        rows.append(r)
    df = pd.DataFrame(rows)
    df.insert(0, "case", label)
    return df
