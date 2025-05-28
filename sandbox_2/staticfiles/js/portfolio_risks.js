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




// document.addEventListener("DOMContentLoaded", () => {
//     const varElem = document.getElementById("monte-carlo-var");
//     const cvarElem = document.getElementById("monte-carlo-cvar");
//
//     const monteCarloContainer = document.querySelector("[data-montecarlo-id]");
//     const portfolioId = monteCarloContainer?.dataset?.montecarloId;
//
//     if (!portfolioId || !varElem || !cvarElem) return;
//
//     fetch(`/monte-carlo-risk/${portfolioId}/`)
//         .then(res => res.ok ? res.json() : Promise.reject("Network response was not ok"))
//         .then(data => {
//             varElem.textContent = data?.VaR ?? "N/A";
//             cvarElem.textContent = data?.CVaR ?? "N/A";
//         })
//         .catch(err => {
//             console.error("Error fetching Monte Carlo risk data:", err);
//             varElem.textContent = "Error";
//             cvarElem.textContent = "Error";
//         });
// });
document.addEventListener("DOMContentLoaded", () => {
    // Get all the new elements
    const varElem = document.getElementById("monte-carlo-var");
    const cvarElem = document.getElementById("monte-carlo-cvar");
    const meanElem = document.getElementById("monte-carlo-mean");
    const stddevElem = document.getElementById("monte-carlo-stddev");
    const chartCanvas = document.getElementById("monteCarloChart");

    const monteCarloContainer = document.querySelector("[data-montecarlo-id]");
    const portfolioId = monteCarloContainer?.dataset?.montecarloId;

    if (!portfolioId || !varElem || !cvarElem || !meanElem || !stddevElem || !chartCanvas) {
        console.error("One or more Monte Carlo elements are missing from the page.");
        return;
    }

    // Function to calculate Gaussian PDF
    function gaussianPDF(x, mean, stdDev) {
        if (stdDev === 0) return x === mean ? Infinity : 0;
        return (1 / (stdDev * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2));
    }

    let monteCarloChartInstance = null; // To hold the chart instance

    fetch(`/monte-carlo-risk/${portfolioId}/`)
        .then(res => res.ok ? res.json() : res.json().then(errData => Promise.reject(errData)))
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            const backendVaRPct = data.VaR_pct;
            const backendCVaRPct = data.CVaR_pct;
            const meanReturnPct = data.mean_return_pct;
            const stdDevReturnPct = data.std_dev_return_pct;

            // Display values, using Math.abs for loss figures
            varElem.textContent = backendVaRPct !== null ? `${Math.abs(backendVaRPct).toFixed(2)}%` : "N/A";
            cvarElem.textContent = backendCVaRPct !== null ? `${Math.abs(backendCVaRPct).toFixed(2)}%` : "N/A";
            meanElem.textContent = meanReturnPct !== null ? `${meanReturnPct.toFixed(2)}%` : "N/A";
            stddevElem.textContent = stdDevReturnPct !== null ? `${stdDevReturnPct.toFixed(2)}%` : "N/A";

            if (meanReturnPct === null || stdDevReturnPct === null || stdDevReturnPct === 0) {
                 const ctx = chartCanvas.getContext('2d');
                 ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
                 ctx.font = "16px Inter, sans-serif";
                 ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-muted');
                 ctx.textAlign = "center";
                 ctx.fillText("Not enough data for distribution.", chartCanvas.width / 2, 50);
                 return;
            }

            const xValues = [];
            const yValues = [];
            const rangeMultiplier = 4;
            const numPoints = 200;
            const minX = meanReturnPct - rangeMultiplier * stdDevReturnPct;
            const maxX = meanReturnPct + rangeMultiplier * stdDevReturnPct;

            for (let i = 0; i <= numPoints; i++) {
                const x = minX + (i / numPoints) * (maxX - minX);
                xValues.push(x);
                yValues.push(gaussianPDF(x, meanReturnPct, stdDevReturnPct));
            }

            const actualVaRPoint = backendVaRPct;
            const actualCVaRPoint = backendCVaRPct;

            if (monteCarloChartInstance) {
                monteCarloChartInstance.destroy();
            }

            const chartContext = chartCanvas.getContext('2d');
            monteCarloChartInstance = new Chart(chartContext, {
                type: 'line',
                data: {
                    labels: xValues.map(x => x.toFixed(2)),
                    datasets: [{
                        data: yValues,
                        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--text-link').trim(),
                        borderWidth: 2,
                        fill: {
                            target: 'origin',
                            above: 'rgba(88, 166, 255, 0.1)',
                        },
                        pointRadius: 0,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: { display: true, text: 'Portfolio Daily Return (%)', color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() },
                            ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() },
                            grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--border-light').trim(), drawOnChartArea: false }
                        },
                        y: {
                            title: { display: true, text: 'Probability Density', color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() },
                            ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim(), precision: 0 },
                            grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--border-light').trim() }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true, mode: 'index', intersect: false },
                        annotation: {
                            annotations: {
                                varLine: { type: 'line', xMin: actualVaRPoint, xMax: actualVaRPoint, borderColor: getComputedStyle(document.documentElement).getPropertyValue('--accent-red').trim(), borderWidth: 2, borderDash: [6, 6], label: { content: `VaR: ${Math.abs(actualVaRPoint).toFixed(2)}%`, enabled: true, position: 'start', backgroundColor: 'rgba(0,0,0,0.7)', yAdjust: -15 }},
                                cvarLine: { type: 'line', xMin: actualCVaRPoint, xMax: actualCVaRPoint, borderColor: getComputedStyle(document.documentElement).getPropertyValue('--accent-red').trim(), borderWidth: 2, label: { content: `CVaR: ${Math.abs(actualCVaRPoint).toFixed(2)}%`, enabled: true, position: 'end', backgroundColor: 'rgba(0,0,0,0.7)', yAdjust: 15 }},
                                meanLine: { type: 'line', xMin: meanReturnPct, xMax: meanReturnPct, borderColor: getComputedStyle(document.documentElement).getPropertyValue('--accent-green').trim(), borderWidth: 1.5, borderDash: [3, 3], label: { content: `Mean`, enabled: true, position: 'center', backgroundColor: 'rgba(0,0,0,0.7)', yAdjust: -30 }},
                                varTailArea: { type: 'box', xMin: minX, xMax: actualVaRPoint, backgroundColor: 'rgba(255, 146, 146, 0.15)', borderColor: 'transparent' }
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error("Error fetching/processing Monte Carlo risk data:", err);
            varElem.textContent = "Error";
            cvarElem.textContent = "Error";
            meanElem.textContent = "Error";
            stddevElem.textContent = "Error";
            const ctx = chartCanvas.getContext('2d');
            ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
            ctx.font = "16px Inter, sans-serif";
            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-muted');
            ctx.textAlign = "center";
            ctx.fillText(err.message || "Error loading chart data.", chartCanvas.width / 2, 50);
        });
});

document.addEventListener('DOMContentLoaded', function () {
    // Tab functionality for Analysis & Tools Hub card
    const analysisHub = document.getElementById('analysis-tools-hub');
    if (analysisHub) {
        const tabLinks = analysisHub.querySelectorAll('.tabs-nav .tab-link');
        const tabPanes = analysisHub.querySelectorAll('.tabs-content .tab-pane');

        tabLinks.forEach(link => {
            link.addEventListener('click', function () {
                const targetTabId = 'tab-' + this.dataset.tab;

                tabLinks.forEach(l => l.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));

                this.classList.add('active');
                const targetPane = analysisHub.querySelector('#' + targetTabId);
                if (targetPane) {
                    targetPane.classList.add('active');
                }
            });
        });
    }

    // ... your other existing JavaScript ...
});


// Store scroll position before unloading the page
window.addEventListener("beforeunload", () => {
    sessionStorage.setItem("scrollPos", window.scrollY);
});

// Restore scroll position after full load
window.addEventListener("load", () => {
    const scrollPos = sessionStorage.getItem("scrollPos");
    if (scrollPos !== null) {
        window.scrollTo(0, parseInt(scrollPos));
    }
});