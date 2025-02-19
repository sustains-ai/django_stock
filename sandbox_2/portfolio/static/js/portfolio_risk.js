// ✅ Ensure Plotly is Loaded Before Running
window.onload = function () {
    console.log("✅ Window Loaded - Initializing Scripts");
    initializeGraphs();
};

// ✅ Portfolio ID Detection & Risk Analysis Handling
document.addEventListener("DOMContentLoaded", function () {
    let portfolioContainer = document.getElementById("portfolio-container");

    if (!portfolioContainer) {
        console.error("❌ Error: Portfolio container not found!");
        return;
    }

    let portfolioId = portfolioContainer.dataset.portfolioId;

    if (!portfolioId) {
        console.error("❌ Error: Portfolio ID is missing or undefined.");
        return;
    }

    console.log(`✅ Detected Portfolio ID: ${portfolioId}`);

    let riskButton = document.getElementById("load-risk-btn");
    if (riskButton) {
        riskButton.addEventListener("click", function () {
            let measure = document.getElementById("risk-selector").value;
            let riskContent = document.getElementById("risk-content");

            // Show loading message
            riskContent.innerHTML = "<p class='text-center text-muted'>Loading...</p>";

            fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        riskContent.innerHTML = `<p class='text-danger'>Error: ${data.error}</p>`;
                    } else {
                        riskContent.innerHTML = `<p class='text-success'>${measure.toUpperCase()}: ${data[measure]}</p>`;
                    }
                })
                .catch(error => {
                    riskContent.innerHTML = "<p class='text-danger'>Failed to load data.</p>";
                    console.error("❌ Error loading risk measure:", error);
                });
        });
    }
});

// ✅ Function to Initialize Graphs
function initializeGraphs() {
    if (typeof Plotly === "undefined") {
        console.error("❌ Plotly is not defined! Ensure the Plotly script is loaded.");
        return;
    }

    console.log("✅ Rendering Portfolio Value Over Time Chart...");
    renderPortfolioValueChart();
}

// ✅ Portfolio Value Over Time Chart
function renderPortfolioValueChart() {
    let portfolioContainer = document.getElementById("portfolio-container");
    if (!portfolioContainer) {
        console.error("❌ Portfolio container not found!");
        return;
    }

    let portfolioValueData = JSON.parse(portfolioContainer.dataset.portfolioValue || "[]");
    if (portfolioValueData.length === 0) {
        console.warn("⚠️ No portfolio value data available.");
        return;
    }

    let trace = {
        x: portfolioValueData.map(data => data.x),
        y: portfolioValueData.map(data => data.y),
        mode: 'lines',
        name: 'Portfolio Value',
        line: { color: '#0ABF53' }
    };

    let layout = {
        title: 'Portfolio Value Over Time',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Value' },
        plot_bgcolor: "#f8f9fa",
        paper_bgcolor: "#ffffff"
    };

    Plotly.newPlot('portfolio-valueoveryears-chart', [trace], layout);
}

// ✅ Ensure Plotly Resizes on Window Resize
window.addEventListener("resize", function () {
    console.log("🔄 Resizing Plotly graph...");
    let chartElement = document.getElementById("portfolio-valueoveryears-chart");
    if (chartElement) {
        Plotly.relayout("portfolio-valueoveryears-chart", { width: window.innerWidth * 0.9 });
    } else {
        console.warn("⚠️ Chart with ID 'portfolio-valueoveryears-chart' not found, skipping resize.");
    }
});