document.addEventListener("DOMContentLoaded", () => {
    const loadAllRisksButton = document.getElementById("load-all-risks-btn");
    const portfolioContainer = document.getElementById("portfolio-container");
    const portfolioId = portfolioContainer?.dataset?.portfolioId;

    // Load risk metrics on button click
    if (loadAllRisksButton && portfolioId) {
        loadAllRisksButton.addEventListener("click", () => {
            loadAllRisksButton.disabled = true;
            loadAllRisksButton.textContent = "Loading...";

            const measures = ["std_dev", "var", "cvar"];
            const riskValues = {};

            Promise.all(measures.map(measure =>
                fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
                    .then(response => {
                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${measure}`);
                        return response.json();
                    })
                    .then(data => {
                        riskValues[measure] = data[measure];
                    })
                    .catch(error => {
                        console.error(`Error fetching ${measure}:`, error);
                        riskValues[measure] = null;
                    })
            ))
            .then(() => {
                document.getElementById("variance-value").textContent = typeof riskValues.std_dev === 'number' ? riskValues.std_dev.toFixed(5) : "N/A";
                document.getElementById("var-value").textContent = typeof riskValues.var === 'number' ? riskValues.var.toFixed(5) : "N/A";
                document.getElementById("cvar-value").textContent = typeof riskValues.cvar === 'number' ? riskValues.cvar.toFixed(5) : "N/A";

                if (typeof renderRiskBarChart === "function") {
                    renderRiskBarChart(riskValues);
                }
            })
            .finally(() => {
                loadAllRisksButton.disabled = false;
                loadAllRisksButton.textContent = "Load All Risk Measures";
            });
    });

    } else {
        if (!loadAllRisksButton) console.warn("Button with ID 'load-all-risks-btn' not found.");
        if (!portfolioId) console.warn("Portfolio ID not found in 'portfolio-container' dataset.");
    }

    // Auto-load risk measures on page load
    fetchAndDisplayRiskMeasures(portfolioId);

    // Load news sentiment on page load
    const newsContainer = document.getElementById("news-container");
    const newsUrl = newsContainer?.getAttribute("data-url");

    if (newsUrl && newsContainer) {
        fetch(newsUrl)
            .then(response => response.json())
            .then(data => {
                newsContainer.innerHTML = "";
                if (!data.news || data.news.length === 0) {
                    newsContainer.innerHTML = "<p class='text-muted'>No news available.</p>";
                    return;
                }

                data.news.forEach(article => {
                    const div = document.createElement("div");
                    div.classList.add("news-item");
                    div.innerHTML = `
                        <p style="margin-bottom: 4px;">
                            <a href="${article.url}" target="_blank" style="color: var(--text-link); text-decoration: none;">
                                ${article.title}
                            </a>
                        </p>
                        <p class="text-muted" style="font-size: 0.85em;">${article.source}</p>
                        <hr style="border: 0.5px solid var(--border-light);">
                    `;
                    newsContainer.appendChild(div);
                });
            })
            .catch(() => {
                newsContainer.innerHTML = "<p class='text-muted'>Failed to load news.</p>";
            });
    }
});

function fetchAndDisplayRiskMeasures(portfolioId) {
    if (!portfolioId) {
        ["variance-value", "var-value", "cvar-value"].forEach(id => {
            const cell = document.getElementById(id);
            if (cell) cell.textContent = "N/A";
        });
        return;
    }

    const measures = ["std_dev", "var", "cvar"];
    const cellMap = {
        std_dev: "variance-value",
        var: "var-value",
        cvar: "cvar-value"
    };

    measures.forEach(measure => {
        const cell = document.getElementById(cellMap[measure]);
        if (cell) cell.textContent = "Loading...";

        fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status} for ${measure}`);
                return response.json();
            })
            .then(data => {
                if (cell) {
                    cell.textContent = typeof data[measure] === 'number' ? parseFloat(data[measure]).toFixed(4) : "N/A";
                }
            })
            .catch(error => {
                console.error(`Error fetching initial ${measure}:`, error);
                if (cell) cell.textContent = "Error";
            });
    });
}
