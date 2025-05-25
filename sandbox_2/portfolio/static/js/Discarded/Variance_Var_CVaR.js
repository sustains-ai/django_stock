// Initialize Charts After Page Load
window.onload = function () {
    initializeGraphs();
    fetchAndDisplayRiskMeasures();  // ✅ Automatically load risk measures
};

// Initialize Graphs (Plotly)
function initializeGraphs() {
    if (typeof Plotly === "undefined") return;

    renderPortfolioValueChart();
    window.addEventListener("resize", resizePortfolioChart);
}

// Portfolio Value Over Time Chart
function renderPortfolioValueChart() {
    const container = document.getElementById("portfolio-container");
    if (!container) return;

    const data = JSON.parse(container.dataset.portfolioValue || "[]");
    if (!data.length) return;

    const trace = {
        x: data.map(d => d.x),
        y: data.map(d => d.y),
        mode: 'lines',
        name: 'Portfolio Value',
        line: { color: '#0ABF53' }
    };

    const layout = {
        title: 'Portfolio Value Over Time',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Value' },
        plot_bgcolor: "#f8f9fa",
        paper_bgcolor: "#ffffff"
    };

    Plotly.newPlot("portfolio-valueoveryears-chart", [trace], layout);
}

// Resize Chart on Window Resize
function resizePortfolioChart() {
    const chart = document.getElementById("portfolio-valueoveryears-chart");
    if (chart) {
        Plotly.relayout(chart, { width: window.innerWidth * 0.9 });
    }
}

// Fetch Risk Measures and Populate Table
function fetchAndDisplayRiskMeasures() {
    const container = document.getElementById("portfolio-container");
    const portfolioId = container?.dataset?.portfolioId;
    if (!portfolioId) return;

    const measures = ["std_dev", "var", "cvar"];
    const cellMap = {
        std_dev: "variance-value",
        var: "var-value",
        cvar: "cvar-value"
    };

    measures.forEach(measure => {
        fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
            .then(res => res.json())
            .then(data => {
                if (data[measure] !== undefined) {
                    const cell = document.getElementById(cellMap[measure]);
                    if (cell) cell.textContent = parseFloat(data[measure]).toFixed(4);
                }
            })
            .catch(err => console.error(`❌ Failed to load ${measure}:`, err));
    });
}
