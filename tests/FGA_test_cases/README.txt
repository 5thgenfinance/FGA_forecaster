Six sample client files for FGA_forecaster (fictional people). Import via Client details > Import client file.
01 baseline couple (workbook defaults) | 02 single pre-retiree | 03 retired couple with pension
04 underfunded late starter with 30-yr mortgage | 05 well-funded high net worth with Sleeve 3 | 06 primary disabled, retired
invalid/99_invalid_example.json should be REJECTED by import (SS age 50 and an unknown field).
All six valid files pass ProjectionInputs validation. They have not been run through the projection, so funding ratios are unknown.
