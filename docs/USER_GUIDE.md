# Fifth Generation Retirement Illustrator — User Guide

This guide explains how to enter a client's details, read the results, try what-if scenarios, and save or share your work. The Illustrator shows whether a client's savings, Social Security and other income are likely to cover their planned spending in retirement, based on the assumptions you enter.

> **Important.** The Illustrator produces a hypothetical illustration based on stated assumptions. It is not a guarantee of future results, and it is not a substitute for professional judgement.

## 1. Quick start

1. Open the app and click the **Client details** button (head icon) in the header. Type the client's name at the top.
2. Fill in the client's dates of birth, retirement dates, income, spending, accounts and Social Security. Use the sidebar for the assumptions (rates, scenarios, Social Security, Sleeve 3).
3. Check the **Valuation date** at the top of the sidebar. It is today's date unless you change it.
4. Read the results in the main panel: the five headline figures, the charts and the year-by-year table.
5. Try the **Scenario sliders** to see how earlier or later retirement, a different rate of return, or different spending changes the picture.
6. Click **Download** to save a CSV, an Excel file or a printable HTML report, and **save the client file** so you can reopen the case later.

Red messages appear next to any field that is missing or out of range. The projection will not run until they are fixed.

## 2. Finding your way around

| Area | What it does |
|---|---|
| Header band | Shows the product name. Holds the **Client details** (head icon) and **Settings** (gear icon) buttons. Stays at the top while you scroll. |
| Sidebar, "Inputs" | The valuation date and grouped input sections. Click a group heading to open or close it. |
| Title block | "Prepared for", the client's name, and the valuation date. |
| Headline figures | Five cards that summarise the result (section 4). |
| Focus year | A slider that picks one year and shows that year's age, resources, cash flow and spending. |
| Charts | Resources against liabilities, yearly cash flow, a funding gauge, the balance sheet, asset mix, income sources and scenarios. |
| Projection table | Year-by-year numbers. Choose which column groups to show. |
| Downloads | CSV, Excel and HTML report. |

## 3. Entering client information

You can enter most client information on the **Client details** page. The assumptions that apply to the whole illustration (mortality table, Social Security, Sleeve 3, rates and scenarios) stay in the sidebar. Amounts are in dollars. Rates are entered as percents: type **3.5** for 3.5%.

Hover over the **?** next to a field for a short explanation.

### Personal
| Field | What to enter |
|---|---|
| Primary date of birth | The primary client's date of birth. |
| Primary gender | M or F. Used to choose the mortality rates. |
| Primary disabled | Tick only if the primary client is disabled. This changes the mortality rates used after retirement. |
| Include spouse | Untick for a single-person plan. The spouse fields are hidden. |
| Spouse date of birth | The spouse's date of birth. |
| Mortality table | The mortality table used to estimate how long the clients are likely to live. RP-2014 is the table currently offered. |
| Retirement status | PRERET if the primary client is still working at the valuation date. RETIRED if already retired. |
| Primary target retirement date | The date the primary client plans to stop working. |
| Spouse target retirement date | The date the spouse plans to stop working. |
| First projection year | The first calendar year of the projection. |

### Income
| Field | What to enter |
|---|---|
| Salary and frequency | The primary client's salary, and whether the figure is Monthly or Yearly. |
| Supplemental salary and frequency | Any other earned income, with its frequency. |
| Post-retirement income and frequency | Regular income expected after the primary client retires (for example a pension or part-time work), with its frequency. |
| Income tax status | PRE or POST, the way the income is stated for tax purposes. |
| Employment risk spread (%) | An extra percentage added to the discount rate for earned income, because salary is less certain than a government bond. |

### Expenses
| Field | What to enter |
|---|---|
| Net expenses and frequency | Living expenses after taxes, with Monthly or Yearly. Mortgage payments are handled separately. |
| Cash cushion months | The number of months of expenses to hold as cash. |
| Cash cushion amount and frequency | The amount of cash set aside at the start. |

### Accounts
Enter the current balance of each account: pre-tax 401k, post-tax 401k, primary traditional IRA, spouse traditional IRA, Roth IRA, brokerage accounts, life insurance cash value, real estate and other precious metals. Brokerage and life insurance cash value are treated as taxable accounts. Real estate and precious metals are treated as real assets that grow with inflation.

### Mortgage
Enter the balance, the interest rate (%) and the number of payments remaining. The monthly payment is calculated for you.

### Social Security (sidebar)
| Field | What to enter |
|---|---|
| Social Security election age | The age the client plans to start benefits, from 62 to 70. |
| Benefit PIA and frequency | The client's Primary Insurance Amount, which is the benefit at full retirement age. |

The benefit is **not adjusted** for the election age. If you change the election age, enter the PIA you want to use for that age.

### Sleeve 3 (sidebar)
| Field | What to enter |
|---|---|
| Sleeve 3 deployed | The amount placed in Sleeve 3 at the start. It is taken out of the brokerage balance. |
| Sleeve 3 payment and frequency | The regular income the sleeve pays. |
| Sleeve 3 income rate (%) | The rate used to work out each year's income from the sleeve balance. |
| Sleeve 3 growth (%) | The rate at which the sleeve balance grows. |

### Rates and scenarios (sidebar)
| Field | What to enter |
|---|---|
| Hurdle rate (%) | The return used to discount the value of the client's assets. It does not affect spending costs, which use Treasury rates. |
| Long-term asset return (%) | The yearly return on the investment accounts. The "Advisor rate of return" slider changes this for what-if testing. |
| 401k growth (%) | The growth rate for the 401k and cash balances. |
| 401k contribution rate | The contribution rate for the 401k. |
| Inflation load (%) | An extra percentage added to the inflation scenario for spending. |
| Inflation scenario | Which inflation path to use for spending. |
| COLA scenario | Which cost-of-living path to use for Social Security and for tax-bracket growth. |

## 4. Reading the results

The five headline cards are:

| Card | Meaning |
|---|---|
| Funding ratio | Today's value of the client's resources divided by today's value of their planned spending. 100% or more means the plan is fully funded on these assumptions. |
| Surplus / (shortfall) | Resources minus spending needs. A figure in brackets is a shortfall. |
| Savings last through | The age at which the savings run out, or "Beyond horizon" if they last through the whole projection. |
| Peak resources | The highest total resources reached, and the year it happens. |
| Retirement | The primary client's age and year of retirement. |

**Resources** include the present value of Social Security, income from Sleeve 3, expected salary, and the account balances. **Spending needs** are living expenses and mortgage payments, valued with Treasury rates and adjusted for the chance that the clients are still alive.

Use the **Focus year** slider to look at a single year. It shows the client's age, total resources, net cash flow and spending for that year.

Underneath, the charts show how resources compare with spending over time, the yearly cash flow, and the mix of accounts. The **projection table** lists each year. Use **Column groups** to show or hide sets of columns such as Timeline, Expenses, Totals and Surplus & cash flow.

When income falls short in a year, the model draws on accounts in a fixed order: cash first, then brokerage, then Sleeve 3, then traditional IRAs, then Roth IRA, then real assets.

## 5. Scenario sliders (what-if)

The sliders let you test alternatives without changing the client's saved information. A banner tells you what has been changed. **Reset sliders** puts everything back.

| Slider | What it does |
|---|---|
| Primary retirement | Moves the primary client's retirement date earlier (−) or later (+) by up to 60 months. |
| Spouse retirement | The same for the spouse (joint plans only). |
| Advisor rate of return (%) | Replaces the long-term asset return for the run. It affects investment growth only; spending costs do not change. |
| Disposable income | Raises or lowers net expenses by a percentage. A positive figure means more spending, so less is left over. Mortgage payments and the cash cushion are unchanged. |

## 6. Saving and opening client files

- **Save:** on the Client details page, choose the option to download the client file. It is a JSON file named after the client, for example *Bryan_and_Melissa_Smith_inputs.json*. It contains the client name, valuation date and all inputs.
- **Open:** drag a saved file onto the upload box or choose it with the file picker. The page shows what the file contains and any problems. **Nothing changes until you click "Apply imported file".**
- **Older files:** files saved before the input names were updated still open normally.
- **Unknown or out-of-range values** in a file are rejected, with a message next to the upload box.

Save the file before you close the tab. Entries you have not saved are lost when the page is refreshed or the session times out. Client information is held for your session only; do not rely on the app to keep it.

## 7. Downloads

| Download | Contents |
|---|---|
| CSV | The full year-by-year projection. |
| XLSX | The same projection as an Excel workbook. |
| HTML report | A printable report with the headline figures and charts, under the firm's branding. Open it in a browser and print or save as PDF. |

## 8. Troubleshooting

| What you see | What to do |
|---|---|
| "Fix the highlighted inputs to run the projection" | Look for the red message next to a field. Correct the value (for example a missing date or a negative amount). |
| A date message such as the retirement date being before the date of birth | Check the dates were entered in the right fields. |
| The warning that retirement date is before the valuation date while status is PRERET | Change the status to RETIRED, or correct the date. |
| A mortality table is "unavailable" and RP-2014 is used instead | The file named a table that is not offered. The illustration uses RP-2014. |
| An imported file does not apply | Read the message beside the upload box. Remove or correct the value it names, then import again. |
| The numbers change when you open the case on a different day | The valuation date defaults to today. Set it to the date you want. |
| A slider seems to do nothing | Press **Reset sliders**, then move one slider at a time. |
| Everything disappeared | The session ended. Open the saved client file to restore the case. |

If something still looks wrong, note the client file, the valuation date and what you expected, and contact the person who maintains the tool.

## 9. Glossary

| Term | Meaning |
|---|---|
| Present value | What a future amount is worth today, after allowing for the time value of money. |
| PIA | Primary Insurance Amount, the monthly Social Security benefit at full retirement age. |
| COLA | Cost-of-living adjustment, the yearly increase applied to Social Security. |
| RMD | Required minimum distribution, the amount the IRS requires to be withdrawn from traditional retirement accounts from a certain age. |
| Survivorship | The estimated chance that the client (or at least one of the couple) is still alive in a given year. |
| Last survivor | A measure that continues until both clients have died, used for spending that continues for the surviving spouse. |
| Hurdle rate | The return used to discount the value of assets. |
| Funding ratio | Resources divided by spending needs, both in today's money. |
| Sleeve 3 | An income-producing portion of the client's portfolio, modelled separately with its own income and growth rates. |

## 10. Disclosure

Hypothetical illustration based on stated assumptions; not a guarantee of future results. Fifth Generation Advisers · Registered Investment Adviser.
