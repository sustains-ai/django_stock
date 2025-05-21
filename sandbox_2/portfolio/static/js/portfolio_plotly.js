function initializeGraphs() {
    if (typeof Plotly === "undefined") return;
    renderPortfolioValueChart();
    window.addEventListener("resize", resizePortfolioChart);
}

function renderPortfolioValueChart() {
    const container = document.getElementById("portfolio-container");
    const data = JSON.parse(container?.dataset?.portfolioValue || "[]");
    if (!data.length) return;

    const trace = {
        x: data.map(d => d.x),
        y: data.map(d => d.y),
        mode: "lines",
        name: "Portfolio Value",
        line: { color: "#0ABF53" }
    };

    const layout = {
        title: "Portfolio Value Over Time",
        xaxis: { title: "Date" },
        yaxis: { title: "Value" },
        plot_bgcolor: "#f8f9fa",
        paper_bgcolor: "#ffffff"
    };

    Plotly.newPlot("portfolio-valueoveryears-chart", [trace], layout);
}

function resizePortfolioChart() {
    const chart = document.getElementById("portfolio-valueoveryears-chart");
    if (chart) {
        Plotly.relayout(chart, { width: window.innerWidth * 0.9 });
    }
}

function renderRiskBarChart(data) {
    const trace = {
        x: Object.keys(data).map(key => key.toUpperCase()),
        y: Object.values(data),
        type: "bar",
        marker: { color: "#0ABF53" }
    };

    const layout = {
        title: "Portfolio Risk Measures",
        xaxis: { title: "Risk Measure" },
        yaxis: { title: "Value" },
        plot_bgcolor: "#f9f9f9",
        paper_bgcolor: "#fff"
    };

    Plotly.newPlot("all-risk-chart", [trace], layout);
}
