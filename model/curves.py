"""Pluggable discount curves. Legacy behavior = OLS regression (Excel FORECAST.LINEAR)."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class DiscountCurve:
    id: str
    maturities: tuple
    rates: tuple
    method: str = "ols_linear"      # 'ols_linear' (Excel parity) | 'interp_linear'
    curve_date: str = ""
    source: str = ""

    def __post_init__(self):
        if len(self.maturities) != len(self.rates) or len(self.rates) < 2:
            raise ValueError("need >=2 matching (maturity, rate) points")
        if self.method not in ("ols_linear", "interp_linear"):
            raise ValueError(f"unknown method {self.method}")

    def rate(self, t: float) -> float:
        """FORECAST.LINEAR(t, rates, maturities) = OLS line over ALL points (not interpolation)."""
        x, y = np.asarray(self.maturities, float), np.asarray(self.rates, float)
        if self.method == "interp_linear":
            return float(np.interp(t, x, y))
        slope, intercept = np.polyfit(x, y, 1)
        return float(intercept + slope * t)

    def disc(self, t: float, timing: str = "EOY") -> float:
        """TREASURYDISC: 1/(1+r)^adjT with EOY (default), MID or BOY timing."""
        tm = timing.upper()
        adj = max(0.0, t - 0.5) if tm in ("MID", "MIDYEAR") else max(0.0, t - 1) if tm == "BOY" else t
        return 1.0 / (1.0 + self.rate(adj)) ** adj

    def with_spread(self, spread: float, id: str | None = None) -> "DiscountCurve":
        return DiscountCurve(id or f"{self.id}+{spread}", self.maturities,
                             tuple(r + spread for r in self.rates), self.method, self.curve_date, self.source)

    @classmethod
    def from_df(cls, df, id, rate_col="Spot Rate", mat_col="Year", **kw):
        return cls(id, tuple(df[mat_col].astype(float)), tuple(df[rate_col].astype(float)), **kw)
