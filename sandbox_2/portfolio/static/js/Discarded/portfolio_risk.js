// Initialize Plotly charts when page fully loads
window.onload = function () {
    initializeGraphs();
};

// Handle portfolio ID and load all risk measures
document.addEventListener("DOMContentLoaded", function () {
    const portfolioContainer = document.getElementById("portfolio-container");
    const portfolioId = portfolioContainer?.dataset?.portfolioId;
    const btn = document.getElementById("load-all-risks-btn");

    if (btn && portfolioId) {
        btn.addEventListener("click", function () {
            const measures = ["std_dev", "var", "cvar"];
            const riskValues = {};

            Promise.all(measures.map(measure =>
                fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
                    .then(response => response.json())
                    .then(data => riskValues[measure] = data[measure])
            )).then(() => {
                // Update table values
                document.getElementById("variance-value").textContent = riskValues.std_dev?.toFixed(5) || "-";
                document.getElementById("var-value").textContent = riskValues.var?.toFixed(5) || "-";
                document.getElementById("cvar-value").textContent = riskValues.cvar?.toFixed(5) || "-";

                // Render risk bar chart
                renderRiskBarChart(riskValues);
            });
        });
    }
});

// Plot portfolio value over time
function initializeGraphs() {
    if (typeof Plotly === "undefined") return;

    renderPortfolioValueChart();
}

// Plotly: Portfolio value chart
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

// Plotly: Risk bar chart
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

// Handle window resize for plotly
window.addEventListener("resize", function () {
    const chart = document.getElementById("portfolio-valueoveryears-chart");
    if (chart) {
        Plotly.relayout(chart, { width: window.innerWidth * 0.9 });
    }
});
