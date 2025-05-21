document.addEventListener("DOMContentLoaded", () => {
    initializeGraphs();
    fetchAndDisplayRiskMeasures();

    const btn = document.getElementById("load-all-risks-btn");
    const container = document.getElementById("portfolio-container");
    const portfolioId = container?.dataset?.portfolioId;

    if (btn && portfolioId) {
        btn.addEventListener("click", () => {
            const measures = ["std_dev", "var", "cvar"];
            const riskValues = {};

            Promise.all(measures.map(measure =>
                fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
                    .then(res => res.json())
                    .then(data => riskValues[measure] = data[measure])
            )).then(() => {
                document.getElementById("variance-value").textContent = riskValues.std_dev?.toFixed(5) || "-";
                document.getElementById("var-value").textContent = riskValues.var?.toFixed(5) || "-";
                document.getElementById("cvar-value").textContent = riskValues.cvar?.toFixed(5) || "-";
                renderRiskBarChart(riskValues);
            });
        });
    }
});

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
            });
    });
}
