# Power BI Dashboard Guide: Quantitative Portfolio Backtesting

This guide provides step-by-step instructions for building a professional, interview-ready Power BI dashboard to visualize the results of the quantitative portfolio backtesting platform.

## 1. Prerequisites

*   **Power BI Desktop:** Download and install the latest version from the [Microsoft Store](https://aka.ms/pbidesktopstore) or the [official website](https://powerbi.microsoft.com/desktop/).
*   **Data Generation:** Ensure you have run the backtesting engine. The dashboard relies on five CSV files generated in the `data/exports/` directory:
    *   `strategy_performance.csv`
    *   `risk_metrics.csv`
    *   `portfolio_weights.csv`
    *   `benchmark_comparison.csv`
    *   `asset_returns.csv`

## 2. Data Import

To import the data into Power BI, follow these exact steps for each of the five CSV files:

1.  Open a new, blank Power BI Desktop file.
2.  On the Home ribbon, click **Get Data** -> **Text/CSV**.
3.  Navigate to your `data/exports/` folder and select the first file (e.g., `strategy_performance.csv`).
4.  In the preview window, verify that the data looks correct.
5.  Click **Load** (or **Transform Data** if you need to ensure column types are correct, such as Date columns being recognized as Dates, and numerical columns as Decimal Numbers).
6.  Repeat steps 2-5 for the remaining four CSV files.

## 3. Data Model & Relationships

Once all tables are loaded, go to the **Model view** (the third icon on the left sidebar). Power BI might auto-detect relationships, but ensure they are configured exactly as follows:

| From Table | From Column | To Table | To Column | Relationship | Cross filter direction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `strategy_performance` | `Strategy` | `risk_metrics` | `Strategy` | Many-to-One (*:1) | Single |
| `portfolio_weights` | `Strategy` | `risk_metrics` | `Strategy` | Many-to-One (*:1) | Single |
| `portfolio_weights` | `Ticker` | `asset_returns` | `Ticker` | Many-to-One (*:1) | Single |

**Note on Dates:** Do not establish a physical relationship using the `Date` column between `strategy_performance` and `portfolio_weights`. Instead, rely on a common Date table if needed, or simply use the `Date` column from `strategy_performance` as your primary slicer, ensuring it filters the necessary visuals.

## 4. DAX Measures

Create a dedicated "Measures" table (Home -> Enter Data -> Name it `_Measures` -> Load) to organize your DAX calculations. Right-click the `_Measures` table and select **New Measure** for each of the following:

```dax
Total Return % = 
SELECTEDVALUE(risk_metrics[Total Return])
// Format as Percentage with 2 decimal places in the Measure tools ribbon
```

```dax
Sharpe Ratio = 
SELECTEDVALUE(risk_metrics[Sharpe Ratio])
// Format as Decimal Number with 2 decimal places
```

```dax
Max Drawdown % = 
SELECTEDVALUE(risk_metrics[Max Drawdown])
// Format as Percentage with 2 decimal places
```

```dax
CAGR % = 
SELECTEDVALUE(risk_metrics[CAGR])
// Format as Percentage with 2 decimal places
```

```dax
Normalized Start Value = 
MINX(
    FILTER(
        ALLSELECTED(strategy_performance), 
        strategy_performance[Date] = MIN(strategy_performance[Date])
    ), 
    [Normalized Value]
)
```

## 5. Page 1: Portfolio Overview

This page provides the high-level executive summary of strategy performance against the benchmark.

*   **KPI Cards (Top Row):** Create four individual Card visuals for the selected strategy. Use the DAX measures created above: `CAGR %`, `Sharpe Ratio`, `Max Drawdown %`, and `Ann. Volatility` (from `risk_metrics`).
*   **Equity Curves (Main Visual):**
    *   **Visual Type:** Line chart
    *   **X-axis:** `strategy_performance[Date]`
    *   **Y-axis:** `strategy_performance[Normalized Value]`
    *   **Legend:** `strategy_performance[Strategy]`
    *   **Styling:** Make the Benchmark (S&P 500) a distinct color (e.g., dark grey) and dashed line to stand out against the colored strategy lines.
*   **Benchmark Comparison (Bottom Right):**
    *   **Visual Type:** Clustered bar chart
    *   **Y-axis:** `risk_metrics[Strategy]`
    *   **X-axis:** `Total Return %` and `CAGR %`
    *   **Note:** Include the benchmark from `benchmark_comparison.csv` for direct visual comparison.

## 6. Page 2: Strategy Comparison

This page drills deeper into the comparative metrics across all tested strategies.

*   **Metric Comparison (Top Half):**
    *   **Visual Type:** Clustered column chart or Clustered bar chart (side-by-side)
    *   **Axis/Category:** `risk_metrics[Strategy]`
    *   **Values:** `Sharpe Ratio`, `Sortino Ratio`, `Calmar Ratio`
*   **Risk vs Return Scatter Plot (Bottom Left):**
    *   **Visual Type:** Scatter chart
    *   **Values/Details:** `risk_metrics[Strategy]`
    *   **X-axis:** `risk_metrics[Ann. Volatility]`
    *   **Y-axis:** `risk_metrics[CAGR]`
    *   **Formatting:** Add a trend line. Strategies in the top-left quadrant (high return, low volatility) are optimal.
*   **Strategy Ranking (Bottom Right):**
    *   **Visual Type:** Table or Matrix
    *   **Columns:** Strategy, CAGR, Sharpe Ratio, Max Drawdown, Beta, Tracking Error. Apply conditional formatting (data bars or color scales) to highlight the best/worst values in each column.

## 7. Page 3: Portfolio Risk & Allocation

This page focuses on the internal mechanics of the portfolios, specifically drawdowns and asset weights.

*   **Drawdown Chart (Top Half):**
    *   **Visual Type:** Area chart
    *   **X-axis:** `strategy_performance[Date]`
    *   **Y-axis:** Calculate Drawdown series dynamically (Current Value / Rolling Peak - 1) or plot the pre-calculated drawdown if available.
    *   **Legend:** `Strategy`
    *   **Formatting:** Invert the Y-axis if possible, or format as negative percentages, shading the area red.
*   **Historical Weights (Bottom Left):**
    *   **Visual Type:** 100% Stacked column chart
    *   **X-axis:** `portfolio_weights[Date]` (aggregated by Month/Year)
    *   **Y-axis:** `portfolio_weights[Weight]`
    *   **Legend:** `portfolio_weights[Ticker]`
    *   **Filter:** Must be filtered to a *single* strategy via slicer to be readable.
*   **Final Allocation (Bottom Right):**
    *   **Visual Type:** Donut chart
    *   **Legend:** `portfolio_weights[Ticker]`
    *   **Values:** `portfolio_weights[Weight]`
    *   **Filter:** Filter to the maximum date in the dataset.

## 8. Filters & Slicers

To make the dashboard interactive, include these slicers on all pages (or use the filter pane):
*   **Date Range Slicer:** Use `strategy_performance[Date]`. Set to "Between" style for a timeline slider. Sync this slicer across all pages.
*   **Strategy Slicer:** Use `strategy_performance[Strategy]`. Use a dropdown or button layout. Sync across pages where appropriate (Note: Page 2 compares all strategies, so only apply this if looking at a single strategy in detail).

## 9. Design & Theme

For a professional, quantitative finance look:
*   **Theme:** Use a dark mode theme (Dark blue/Grey backgrounds with bright accent colors) or a clean, minimalist light theme (White/Light Grey with Navy and Teal accents).
*   **Colors:** Go to View -> Themes -> Customize current theme.
    *   Backgrounds: `#F3F4F6` (Light grey) or `#1E293B` (Dark slate)
    *   Primary Data Colors: `#2563EB` (Blue), `#10B981` (Green), `#F59E0B` (Amber)
    *   Benchmark Color: `#64748B` (Grey - consistent across all charts)
*   **Typography:** Use professional fonts like `Segoe UI`, `DIN`, or `Helvetica`. Keep font sizes readable (10-12pt for axes, 14-16pt for titles).

## 10. Troubleshooting

*   **Error:** "The column 'Date' cannot be found."
    *   **Fix:** Ensure the CSV import recognized the column as a Date type in Power Query (Transform Data). If it imported as Text, change the data type to Date.
*   **Error:** Cross-filtering isn't working between visuals.
    *   **Fix:** Check your Data Model (Step 3). Ensure relationships are active and the Cross filter direction is appropriate (usually Single, pointing towards the fact table).
*   **Error:** Slicers affect charts they shouldn't.
    *   **Fix:** Select the Slicer, go to Format -> Edit interactions, and disable filtering for specific visuals (like the Strategy Comparison charts on Page 2).
