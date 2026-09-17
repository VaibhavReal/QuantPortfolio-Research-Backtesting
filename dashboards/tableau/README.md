# Tableau Dashboard Guide: Quantitative Portfolio Backtesting

This guide outlines the steps to create an interactive and visually appealing Tableau dashboard for the quantitative portfolio backtesting project. This is designed to be presentation-ready for final year project interviews.

## 1. Prerequisites

*   **Software:** Install [Tableau Desktop](https://www.tableau.com/products/desktop/download) (if you have an academic license) or the free [Tableau Public](https://public.tableau.com/en-us/s/download).
*   **Data Generation:** Ensure the backtesting script has run successfully and generated the necessary CSV files in the `data/exports/` directory:
    *   `strategy_performance.csv`
    *   `risk_metrics.csv`
    *   `portfolio_weights.csv`
    *   `benchmark_comparison.csv`
    *   `asset_returns.csv`

## 2. Data Connection

1.  Open Tableau. Under **Connect** -> **To a File**, select **Text file**.
2.  Navigate to your `data/exports/` directory and open `strategy_performance.csv`.
3.  In the Data Source tab, drag the remaining CSV files from the left pane into the canvas to establish connections (relationships).

## 3. Relationships & Data Model

Construct Tableau's logical data model by relating the tables using common fields:

1.  Start with `strategy_performance` as the central table.
2.  Drag `risk_metrics` onto the canvas next to `strategy_performance`. Tableau will prompt you to edit the relationship.
    *   Match: `Strategy` = `Strategy`
3.  Drag `portfolio_weights` onto the canvas.
    *   Match: `Strategy` = `Strategy` (Note: If analyzing specific dates, you might need a cross-database join or blend on Date, but standard relationships on Strategy are best for overall metrics).
4.  Drag `asset_returns` onto the canvas.
    *   Match with `portfolio_weights` on: `Ticker` = `Ticker`

## 4. Calculated Fields

To create dynamic visuals, we need specific Calculated Fields. In any worksheet, click the dropdown arrow next to the search bar in the Data pane and select **Create Calculated Field**.

**Cumulative Return %**
```tableau
// Formatted as Percentage
[Normalized Value] - 1
```

**Risk-Adjusted Return**
```tableau
// Maps the Sharpe Ratio for easy use in views
[Sharpe Ratio]
```

**Drawdown**
```tableau
// Calculates the drawdown series using a table calculation
// Needs to be computed along Date
[Normalized Value] / WINDOW_MAX(MAX([Normalized Value])) - 1
```

**Active Return (Example LOD)**
```tableau
// Assuming you blended or joined benchmark daily returns
[Daily Return] - {FIXED [Date]: SUM(IIF([Strategy]='Benchmark', [Daily Return], 0))}
```

## 5. Worksheets

Create the following individual worksheets (tabs at the bottom) to serve as the building blocks of your dashboards.

### Sheet 1: Equity Curves
*   **Columns:** `Date` (Right-click -> Continuous, Exact Date)
*   **Rows:** `Normalized Value` (Continuous)
*   **Marks Card:**
    *   Color: `Strategy`
*   **Formatting:** Right-click the axis and ensure it doesn't include zero to emphasize the curves. Make the benchmark line a neutral, dashed grey line.

### Sheet 2: Risk Metrics Comparison
*   **Columns:** Measure Names
*   **Rows:** `Strategy`
*   **Marks Card:**
    *   Text: Measure Values
*   **Details:** Filter Measure Names to show only: `Total Return`, `CAGR`, `Ann. Volatility`, `Sharpe Ratio`, `Max Drawdown`. Use a Bar chart or a highlight table.

### Sheet 3: Portfolio Weights Heatmap
*   **Columns:** `Ticker`
*   **Rows:** `Date` (Continuous Month/Year)
*   **Marks Card:**
    *   Type: Square
    *   Color: `Weight` (Use a Blue-White-Red diverging palette, or just single sequential color)
*   **Filter:** Must be filtered to a single Strategy to make sense.

### Sheet 4: Drawdown Chart
*   **Columns:** `Date` (Continuous Exact Date)
*   **Rows:** `Drawdown` (Calculated Field from Step 4)
*   **Marks Card:**
    *   Type: Area
    *   Color: `Strategy`
*   **Table Calculation:** Edit the `Drawdown` table calculation to Compute Using -> Specific Dimensions -> Date.

### Sheet 5: Risk-Return Scatter Plot
*   **Columns:** `Ann. Volatility` (Continuous Dimension or AVG)
*   **Rows:** `CAGR` (Continuous Dimension or AVG)
*   **Marks Card:**
    *   Type: Circle
    *   Color: `Strategy`
    *   Label: `Strategy`
*   **Analytics Pane:** Drag a Reference Line to average Volatility and average CAGR to create quadrants.

## 6. Dashboard Assembly

Combine the sheets into cohesive presentation dashboards.

**Dashboard 1: Overview & Performance**
*   **Size:** Automatic or Fixed Desktop (e.g., 1366x768).
*   **Layout:**
    *   Top: Title and KPIs (create simple sheets for KPI numbers).
    *   Middle: Sheet 1 (Equity Curves) taking up majority space.
    *   Bottom: Sheet 2 (Risk Metrics Table).

**Dashboard 2: Risk & Allocation Deep Dive**
*   **Layout:**
    *   Top Left: Sheet 5 (Risk-Return Scatter).
    *   Top Right: Sheet 4 (Drawdown Chart).
    *   Bottom: Sheet 3 (Weights Heatmap).

## 7. Filters

To make the dashboards interactive:
1.  Go to Dashboard 1. Select the Equity Curves sheet.
2.  Click the dropdown arrow on the sheet's border -> Filters -> `Date`.
3.  Click the dropdown on the newly added filter card -> Apply to Worksheets -> **All Using This Data Source**.
4.  Add a `Strategy` filter similarly. On Dashboard 2, ensure the Strategy filter applies to the Heatmap and Drawdown charts, allowing the user to select one strategy at a time for deeper analysis.

## 8. Formatting Tips

*   **Tooltips:** Edit tooltips for all charts to be readable. Remove unnecessary fields and format numbers (e.g., percentages to 2 decimal places).
    *   *Example Tooltip:* `<Strategy> on <Date>: Portfolio Value: <Normalized Value>`
*   **Colors:** Use a consistent color palette across all sheets. Assign a specific color to Equal Weight, Minimum Variance, Risk Parity, and the Benchmark. Go to **Format -> Workbook** to set global fonts (e.g., Tableau Book).
*   **Cleanliness:** Hide all worksheet titles on the dashboard if they are redundant. Hide axes titles if the meaning is obvious.

## 9. Exporting to Tableau Public (Optional)

If using Tableau Public, or presenting via the web:
1.  Go to **Server** -> **Tableau Public** -> **Save to Tableau Public...**
2.  Log in to your Tableau Public account.
3.  Ensure data extracts are created (Tableau Public requires extracts, not live connections to local files).
4.  Publish and copy the URL to include in your project report or portfolio.
