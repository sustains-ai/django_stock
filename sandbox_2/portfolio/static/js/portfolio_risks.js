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

            const riskPromises = measures.map(measure =>
                fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
                    .then(response => {
                        if (!response.ok) throw new Error(`HTTP error for ${measure}`);
                        return response.json();
                    })
                    .then(data => { riskValues[measure] = data[measure]; })
                    .catch(err => {
                        console.error(`Error fetching ${measure}:`, err);
                        riskValues[measure] = null;
                    })
            );

            const treasuryYieldPromise = fetch(`/fetch-treasury-yield/${portfolioId}/`)
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error for treasury_yield`);
                    return response.json();
                })
                .then(data => {
                    riskValues.treasury_yield = data?.yield ?? null;
                })
                .catch(err => {
                    console.error("Error fetching treasury yield:", err);
                    riskValues.treasury_yield = null;
                });

            Promise.all([...riskPromises, treasuryYieldPromise])
                .then(() => {
                    document.getElementById("variance-value").textContent = typeof riskValues.std_dev === 'number' ? riskValues.std_dev.toFixed(5) : "N/A";
                    document.getElementById("var-value").textContent = typeof riskValues.var === 'number' ? riskValues.var.toFixed(5) : "N/A";
                    document.getElementById("cvar-value").textContent = typeof riskValues.cvar === 'number' ? riskValues.cvar.toFixed(5) : "N/A";
                    document.getElementById("treasury-yield-value").textContent = typeof riskValues.treasury_yield === 'number' ? riskValues.treasury_yield.toFixed(2) + "%" : "N/A";

                    if (typeof renderRiskBarChart === "function") renderRiskBarChart(riskValues);
                })
                .finally(() => {
                    loadAllRisksButton.disabled = false;
                    loadAllRisksButton.textContent = "Load All Risk Measures";
                });
        });
    }

    fetchAndDisplayRiskMeasures(portfolioId);

    const newsContainer = document.getElementById("news-container");
    const newsUrl = newsContainer?.getAttribute("data-url");

    if (newsUrl && newsContainer) {
        fetch(newsUrl)
            .then(res => res.json())
            .then(data => {
                newsContainer.innerHTML = "";
                if (!data.news?.length) {
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

    const exchangeContainer = document.getElementById("exchange-rate-container");
    const url = exchangeContainer?.getAttribute("data-url");

    if (exchangeContainer && url) {
        fetch(url)
            .then(res => res.json())
            .then(data => {
                exchangeContainer.innerHTML = "";
                if (!data.exchange_rates?.length) {
                    exchangeContainer.innerHTML = "<p class='text-muted'>No exchange rate data available.</p>";
                    return;
                }

                data.exchange_rates.forEach(rate => {
                    const div = document.createElement("div");
                    div.classList.add("exchange-rate-item");
                    div.innerHTML = `
                        <p style="margin-bottom: 2px;">${rate.from} → ${rate.to}</p>
                        <p style="font-size: 1.2em;">${rate.rate ? parseFloat(rate.rate).toFixed(4) : 'N/A'}</p>
                        <hr style="border: 0.5px solid var(--border-light);">
                    `;
                    exchangeContainer.appendChild(div);
                });
            })
            .catch(() => {
                exchangeContainer.innerHTML = "<p class='text-muted'>Failed to load exchange rate data.</p>";
            });
    }
});

function fetchAndDisplayRiskMeasures(portfolioId) {
    if (!portfolioId) {
        ["variance-value", "var-value", "cvar-value", "treasury-yield-value"].forEach(id => {
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
                if (!response.ok) throw new Error(`HTTP error for ${measure}`);
                return response.json();
            })
            .then(data => {
                if (cell) cell.textContent = typeof data[measure] === 'number' ? data[measure].toFixed(4) : "N/A";
            })
            .catch(err => {
                console.error(`Error fetching ${measure}:`, err);
                if (cell) cell.textContent = "Error";
            });
    });

    // Fetch treasury yield separately
    fetch(`/fetch-treasury-yield/${portfolioId}/`)
        .then(res => res.json())
        .then(data => {
            const cell = document.getElementById("treasury-yield-value");
            if (cell) {
                cell.textContent = typeof data?.yield === 'number' ? data.yield.toFixed(2) + "%" : "N/A";
            }
        })
        .catch(err => {
            console.error("Error fetching treasury yield:", err);
            const cell = document.getElementById("treasury-yield-value");
            if (cell) cell.textContent = "Error";
        });
}
