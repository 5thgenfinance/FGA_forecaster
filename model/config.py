"""Centralized constants. Source: hard-coded values inside the Excel LAMBDAs (spec sec. 3, 10 #11).
Update TAX_YEAR_LABEL and the values below when annual figures change."""
TAX_YEAR_LABEL = "workbook-2026-11-03"
MAX_HORIZON_YEARS = 64
MAX_MORTALITY_AGE = 120

# TaxEst / IraFill
STD_DED_SINGLE = 16_100
STD_DED_MFJ = 32_200
NIIT_RATE = 0.038
NIIT_THRESHOLD_SINGLE = 200_000
NIIT_THRESHOLD_MFJ = 250_000
LTCG_RATE_15 = 0.15
LTCG_RATE_20 = 0.20
BASE_ORDINARY_RATE = 0.10  # implicit first bracket starting at zero

# ROTH_LIMIT
ROTH_BASE = 7_500
ROTH_CATCHUP = 1_100
ROTH_PHASEOUT_LO_SINGLE = 153_000
ROTH_PHASEOUT_LO_MFJ = 242_000
ROTH_RANGE_SINGLE = 15_000
ROTH_RANGE_MFJ = 10_000
ROTH_CATCHUP_AGE = 50
ROTH_INFLATION = 0.03           # Projection!CF uses 3%
ROTH_INFLATION_DEFAULT = 0.025  # LAMBDA default when [infl] omitted

# SLEEVEFEE: (tier1 <=500k, tier2 500k-2M, tier3 >2M)
FEE_TIER_BREAKS = (500_000, 2_000_000)
FEE_SCHEDULE = {
    1: (0.0, 0.0, 0.0),
    2: (0.0075, 0.006, 0.005),
    3: (0.0075, 0.006, 0.005),
    4: (0.0125, 0.011, 0.01),
    5: (0.0125, 0.011, 0.01),
}

# Projection sheet
PRETAX_DRAW_PCT = 0.06        # Projection!BD3
CASH_RESERVE_MONTHS = 2       # Projection!CG5
WITHDRAWAL_ELIGIBLE_AGE = 59  # AW/BA flag is age > 59
RMD_FLOOR_AGE_FACTOR = 2.0    # age >= 120
SSI_ANNUAL_SALARY_BASIS = 3050 * 12
MORTGAGE_REMAINING_PMTS_DEFAULT = 12 * 5
