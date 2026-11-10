"""Phase 3 - forward (balance-dependent) projection loop.

Reproduces the Excel 'Projection' Phase B columns: Sleeve 3 income (AI), ages and withdrawal flags
(AV/AW/AZ/BA), RMDs (AX/BB), AGI (AM), IRA headroom (AN), planned distributions (BD/BE), tax (AO/AP),
after-tax income (BY/BZ/CA), cash flow (CD), contribution waterfall (CF:CH), distribution waterfall
(CJ:CO, CQ) and the account roll-forwards (AT/AU/AY/BI:BN/BV/BW).

The PV/backward columns (AJ, AK, AQ, AR, CC, CR, dashboard feed, summary) are Phase 4.
Dependency order inside each year (no circularity): RMD -> AI -> AM -> AN -> BD -> BE -> AO -> BY..CD
-> CF..CH -> CJ..CO -> balances.  Prior-year balances feed the current year.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from . import config as C
from .engine import ModelTables, run_vectors
from .helpers import attained_age, pretax_draw, rmd
from .inputs import ProjectionInputs
from .tax import TaxTables, ira_fill, roth_limit, tax_est

FORWARD_COLUMNS = ["AI", "AM", "AN", "AO", "AP", "AT", "AU", "AV", "AW", "AX", "AY", "AZ", "BA", "BB", "BD", "BE",
                   "BI", "BJ", "BK", "BL", "BM", "BN", "BV", "BW", "BY", "BZ", "CA", "CD", "CF", "CG", "CH",
                   "CJ", "CK", "CL", "CM", "CN", "CO", "CQ"]

@dataclass
class ForwardTables:
    """Tax and RMD tables exported in Phase 0."""
    tax: TaxTables
    lurmd: dict

    @classmethod
    def from_csv_dir(cls, path) -> "ForwardTables":
        p = Path(path)
        u = pd.read_csv(p / "tblLURMD.csv")
        return cls(TaxTables.from_csv_dir(p), {int(a): float(f) for a, f in zip(u["attained_age"], u["factor"])})

def opening_balances(inputs: ProjectionInputs) -> dict:
    """Projection row 5 (AT5..BN5)."""
    bk = inputs.sleeve3_balance
    bl = inputs.cash_cushion_balance
    return {"AT": inputs.pretax_401k, "AU": inputs.primary_trad_ira, "AY": inputs.spouse_trad_ira, "BI": inputs.roth_401k,
            "BJ": inputs.roth_ira, "BK": bk, "BL": bl, "BM": inputs.brokerage_net - bk - bl,
            "BN": inputs.real_estate + inputs.other_PMs}

def run_forward(inputs: ProjectionInputs, vec: pd.DataFrame, ft: ForwardTables,
                draw_pct: float = C.PRETAX_DRAW_PCT, cash_months: float = C.CASH_RESERVE_MONTHS,
                roth_infl: float = C.ROTH_INFLATION) -> pd.DataFrame:
    """Run the forward loop on top of the Phase-A vectors (`vec` from engine.run_vectors)."""
    n = len(vec)
    joint = inputs.joint
    v = {c: vec[c].to_numpy(float) for c in ["A", "B", "C", "D", "E", "G", "H", "R", "J", "V", "AC", "AD", "AG"]}
    out = {c: np.zeros(n) for c in FORWARD_COLUMNS}
    ob = opening_balances(inputs)
    prev = dict(ob)
    g401, ltror, s3irr = inputs.growth_rate_401k, inputs.lt_return_rate, inputs.sleeve3_growth_rate
    for t in range(n):
        yr = int(v["B"][t])
        # ages / eligibility
        if t == 0:
            av = attained_age(inputs.primary_dob, date(yr - 1, 12, 31))
            az = attained_age(inputs.spouse_dob, date(yr - 1, 12, 31)) if joint else np.nan
        else:
            av, az = out["AV"][t - 1] + 1, out["AZ"][t - 1] + 1
        aw = 1.0 if av > C.WITHDRAWAL_ELIGIBLE_AGE else 0.0
        ba = 1.0 if (joint and az > C.WITHDRAWAL_ELIGIBLE_AGE) else 0.0
        # RMDs on prior-year balances
        ax = rmd(inputs.primary_dob, yr, prev["AU"], ft.lurmd)
        bb = rmd(inputs.spouse_dob, yr, prev["AY"], ft.lurmd) if joint else 0.0
        # income
        ac, ad, vs, rr = v["AC"][t], v["AD"][t], v["V"][t], v["R"][t]
        ai = prev["BK"] * inputs.sleeve3_income_rate
        am = ac + ad + ai + ax + bb + vs
        an = ira_fill(ft.tax, ac + ad + ax + bb + 0.2 * ai, 0.8 * ai, joint, rr - 1, 1, prev["AU"] + prev["AY"], 1)
        bd = pretax_draw(an - ax, prev["AU"], draw_pct, aw) + ax
        be = (pretax_draw(an - bb - bd, prev["AY"], draw_pct, ba) + bb) if joint else 0.0
        ao = tax_est(ft.tax, ac + ad + 0.2 * ai + bd + be + vs, 0.8 * ai, joint, rr - 1, 1)
        ap = ao / am if am != 0 else np.nan
        by = ac + ai + bd + be + vs + ad
        bz = ao
        ca = by - bz
        cd = ca - v["G"][t] - v["H"][t]
        # contributions
        d_age = v["D"][t] if joint else 0.0
        cf = max(min(cd, roth_limit(am, joint, v["C"][t], d_age, v["A"][t], roth_infl)), 0.0)
        cg = max(min(cd - cf, (v["G"][t] + v["H"][t]) * cash_months / 12), 0.0)
        ch = max(cd - cf - cg, 0.0)
        # distribution waterfall (cash -> brokerage -> sleeve 3 -> trad IRA -> Roth -> real assets)
        cj = min(-min(0.0, cd), prev["BL"])
        ck = min(max(0.0, -(cd + cj)), prev["BM"])
        cl = min(max(-(cj + ck + cd), 0.0), prev["BK"])
        cm = min(max(-(cj + ck + cd + cl), 0.0), prev["AU"] + prev["AY"])
        cn = min(max(-(cj + ck + cd + cm + cl), 0.0), prev["BJ"])
        co = min(max(-(cj + ck + cd + cm + cl + cn), 0.0), prev["BN"])
        cq = cj + ck + cl + cm + cn + co
        # balances
        agt = v["AG"][t]
        at = prev["AT"] * (0.0 if agt == 0 else 1 + g401)
        au = prev["AU"] * (1 + ltror) - (bd + cm) * (1 + ltror) ** 0.5
        if agt == 0:
            au += prev["AT"] * (1 + ltror) ** (1 - agt)
        if t > 0:
            au = max(au, 0.0)
        ay = prev["AY"] * (1 + ltror) - be
        bi = prev["BI"] * (1 + g401)
        bj = prev["BJ"] * (1 + ltror) + (cf - cn) * (1 + ltror) ** 0.5
        bk = prev["BK"] * (1 + s3irr) - cl * (1 + s3irr) ** 0.5
        bl = prev["BL"] * (1 + g401) + (cg - cj) * (1 + g401) ** 0.5
        bm = max(0.0, prev["BM"] * (1 + ltror) + (ch - ck) * (1 + ltror) ** 0.5)
        bn = prev["BN"] * v["E"][t] - co
        bv = at + au + ay + bi + bj + bk + bl + bm + bn
        bw = bv * v["J"][t]
        row = dict(AI=ai, AM=am, AN=an, AO=ao, AP=ap, AT=at, AU=au, AV=av, AW=aw, AX=ax, AY=ay, AZ=az, BA=ba,
                   BB=bb, BD=bd, BE=be, BI=bi, BJ=bj, BK=bk, BL=bl, BM=bm, BN=bn, BV=bv, BW=bw, BY=by, BZ=bz,
                   CA=ca, CD=cd, CF=cf, CG=cg, CH=ch, CJ=cj, CK=ck, CL=cl, CM=cm, CN=cn, CO=co, CQ=cq)
        for k, val in row.items():
            out[k][t] = val
        prev = {"AT": at, "AU": au, "AY": ay, "BI": bi, "BJ": bj, "BK": bk, "BL": bl, "BM": bm, "BN": bn}
    return pd.DataFrame(out)[FORWARD_COLUMNS]

def run_through_phase3(inputs: ProjectionInputs, tables: ModelTables, ft: ForwardTables, as_of_date: date,
                       inflation=None, curve=None, legacy_quirks: bool = True, **kw) -> tuple[pd.DataFrame, dict]:
    """Phase A vectors + Phase B forward loop in one DataFrame (Excel column codes)."""
    vec, meta = run_vectors(inputs, tables, as_of_date, inflation, curve, legacy_quirks)
    fwd = run_forward(inputs, vec, ft, **kw)
    df = pd.concat([vec, fwd], axis=1)
    meta = dict(meta, opening_balances=opening_balances(inputs),
                total_assets_BV1=float(df["BV"].iloc[0]), cash_flow_CD1=float(df["CD"].iloc[0]),
                tax_AO1=float(df["AO"].iloc[0]))
    return df, meta
