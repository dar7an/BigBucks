/* Charts consume /api/series and /api/compare. Dates are chronological; cumulative is P_t/P_0 − 1. */
const BigBucksCharts = (() => {
  const ink = "#1a3d32";
  const muted = "#5c736b";
  const brand = "#1f5c47";
  const spy = "#3a4d8f";
  const grid = "rgba(26, 61, 50, 0.12)";
  const paper = "rgba(0,0,0,0)";

  const baseLayout = {
    font: { family: "system-ui, sans-serif", color: ink, size: 13 },
    paper_bgcolor: paper,
    plot_bgcolor: paper,
    margin: { t: 36, r: 16, b: 48, l: 56 },
    xaxis: { gridcolor: grid, zerolinecolor: grid },
    yaxis: { gridcolor: grid, zerolinecolor: grid },
    legend: { orientation: "h", y: 1.12 },
  };

  function pctTick() {
    return { tickformat: ".0%", gridcolor: grid, zerolinecolor: grid };
  }

  async function getJson(url) {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("Could not load chart data.");
    return res.json();
  }

  async function quote(ticker) {
    const data = await getJson(`/api/series/${encodeURIComponent(ticker)}`);
    const dates = data.dates;
    const prices = data.adj_close;
    const dailyDates = dates.slice(1);
    const daily = [];
    for (let i = 1; i < prices.length; i += 1) {
      daily.push(prices[i] / prices[i - 1] - 1);
    }

    Plotly.newPlot(
      "plotchart",
      [{ x: dates, y: prices, type: "scatter", mode: "lines", line: { color: brand, width: 2 }, name: ticker }],
      { ...baseLayout, title: `${ticker} adjusted close`, yaxis: { ...baseLayout.yaxis, tickprefix: "$" } },
      { responsive: true, displaylogo: false }
    );

    Plotly.newPlot(
      "DailyChangeScatterChart",
      [{ x: dailyDates, y: daily, mode: "markers", type: "scatter", marker: { color: brand, size: 6, opacity: 0.65 }, name: "Daily return" }],
      { ...baseLayout, title: `${ticker} daily simple returns`, yaxis: pctTick() },
      { responsive: true, displaylogo: false }
    );

    Plotly.newPlot(
      "returnHistogram",
      [{ x: daily, type: "histogram", marker: { color: brand }, opacity: 0.85 }],
      { ...baseLayout, title: `Distribution of ${ticker} daily returns`, xaxis: pctTick(), yaxis: { title: "Count", gridcolor: grid } },
      { responsive: true, displaylogo: false }
    );

    const today = daily.slice(1);
    const yesterday = daily.slice(0, -1);
    Plotly.newPlot(
      "autocorrelationChart",
      [{ x: yesterday, y: today, mode: "markers", type: "scatter", marker: { color: brand, size: 6, opacity: 0.65 } }],
      {
        ...baseLayout,
        title: "Today’s return vs yesterday’s",
        xaxis: { ...pctTick(), title: "Yesterday" },
        yaxis: { ...pctTick(), title: "Today" },
      },
      { responsive: true, displaylogo: false }
    );
  }

  function regression(x, y) {
    const n = y.length;
    if (n < 2) return x.map(() => 0);
    let sx = 0;
    let sy = 0;
    let sxy = 0;
    let sxx = 0;
    for (let i = 0; i < n; i += 1) {
      sx += x[i];
      sy += y[i];
      sxy += x[i] * y[i];
      sxx += x[i] * x[i];
    }
    const denom = n * sxx - sx * sx;
    const slope = denom === 0 ? 0 : (n * sxy - sx * sy) / denom;
    const intercept = (sy - slope * sx) / n;
    return x.map((v) => slope * v + intercept);
  }

  async function compare(ticker) {
    const data = await getJson(`/api/compare/${encodeURIComponent(ticker)}`);
    Plotly.newPlot(
      "comparisonChartSPY",
      [
        { x: data.dates, y: data.a_cum, type: "scatter", mode: "lines", name: ticker, line: { color: brand, width: 2 } },
        { x: data.dates, y: data.b_cum, type: "scatter", mode: "lines", name: "SPY", line: { color: spy, width: 2 } },
      ],
      {
        ...baseLayout,
        title: `${ticker} vs SPY · cumulative return from t0`,
        yaxis: { ...pctTick(), title: "Return from first overlapping close" },
      },
      { responsive: true, displaylogo: false }
    );

    Plotly.newPlot(
      "dailyChangeChartSPY",
      [
        { x: data.daily_dates, y: data.a_daily, type: "scatter", mode: "lines", name: ticker, line: { color: brand, width: 1.5 } },
        { x: data.daily_dates, y: data.b_daily, type: "scatter", mode: "lines", name: "SPY", line: { color: spy, width: 1.5 } },
      ],
      { ...baseLayout, title: "Daily simple returns", yaxis: pctTick() },
      { responsive: true, displaylogo: false }
    );

    Plotly.newPlot(
      "scatterChartSPY",
      [
        {
          x: data.b_daily,
          y: data.a_daily,
          mode: "markers",
          type: "scatter",
          name: "Sessions",
          marker: { color: brand, size: 6, opacity: 0.55 },
        },
        {
          x: data.b_daily,
          y: regression(data.b_daily, data.a_daily),
          mode: "lines",
          name: "OLS fit",
          line: { color: spy, width: 2 },
        },
      ],
      {
        ...baseLayout,
        title: `${ticker} vs SPY daily returns`,
        xaxis: { ...pctTick(), title: "SPY" },
        yaxis: { ...pctTick(), title: ticker },
      },
      { responsive: true, displaylogo: false }
    );
  }

  function frontier(points, vol, ret) {
    const canvas = document.getElementById("frontier");
    if (!canvas || typeof Chart === "undefined") return;
    const data = (points || []).map(([x, y]) => ({ x, y }));
    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [
          {
            label: "Unconstrained frontier",
            data,
            showLine: true,
            borderColor: brand,
            backgroundColor: "transparent",
            pointRadius: 3,
            borderWidth: 2,
          },
          {
            label: "Your book",
            data: vol == null || ret == null ? [] : [{ x: vol, y: ret }],
            backgroundColor: "#b42318",
            borderColor: "#b42318",
            pointRadius: 7,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: ink, font: { family: "system-ui" } } },
        },
        scales: {
          x: {
            title: { display: true, text: "Annualized volatility", color: muted },
            ticks: {
              color: muted,
              callback: (v) => `${(v * 100).toFixed(0)}%`,
            },
            grid: { color: grid },
          },
          y: {
            title: { display: true, text: "Annualized expected return", color: muted },
            ticks: {
              color: muted,
              callback: (v) => `${(v * 100).toFixed(0)}%`,
            },
            grid: { color: grid },
          },
        },
      },
    });
  }

  return { quote, compare, frontier };
})();
