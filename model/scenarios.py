"""Pluggable inflation scenarios. Series are FRACTIONS (0.025 = 2.5%); the legacy table is in percent."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class InflationScenario:
    id: str
    cpi: tuple
    cola: tuple
    source: str = ""
    as_of: str = ""

    def __post_init__(self):
        if len(self.cpi) != len(self.cola) or not self.cpi:
            raise ValueError("cpi and cola must be same non-zero length")
        if max(max(self.cpi), max(self.cola)) > 1.0:
            raise ValueError("values look like percents; pass fractions")

    def expense_factors(self, load: float, n: int) -> np.ndarray:
        """Projection!E = CPI + InflationLoad + 1, one per projection year."""
        return 1.0 + self._take(self.cpi, n) + load

    def cola_factors(self, n: int) -> np.ndarray:
        """Projection!Q = COLA + 1."""
        return 1.0 + self._take(self.cola, n)

    @staticmethod
    def _take(series, n):
        if n > len(series):
            raise ValueError(f"scenario covers {len(series)} years; {n} required")
        return np.asarray(series[:n], float)

    @classmethod
    def from_legacy_table(cls, df, cpi_col: str, cola_col: str, id: str | None = None):
        return cls(id or f"{cpi_col}/{cola_col}", tuple(df[cpi_col] / 100.0), tuple(df[cola_col] / 100.0),
                   source="tblInflation")

    @classmethod
    def constant(cls, cpi: float, cola: float | None = None, n: int = 64, id: str = "constant"):
        return cls(id, (cpi,) * n, (cpi if cola is None else cola,) * n)

    def shifted(self, bps: float):
        d = bps / 1e4
        return InflationScenario(f"{self.id}{bps:+g}bp", tuple(c + d for c in self.cpi),
                                 tuple(c + d for c in self.cola), self.source, self.as_of)
