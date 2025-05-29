/**
 * @file portfolio_dashboard_main.js
 * @description This script handles various interactive and data-driven components of the portfolio dashboard page,
 *              including key metrics, news, exchange rates, Monte Carlo analysis, treasury yields, tabs, and scroll management.
 */

// Wait for the entire HTML document to be fully loaded and parsed.
document.addEventListener("DOMContentLoaded", () => {
    // --- Central Portfolio ID ---
    const mainPortfolioContainer = document.getElementById("portfolio-container");
    const globalPortfolioId = mainPortfolioContainer?.dataset?.portfolioId;

    // --- Initialize All Modules/Sections ---
    if (globalPortfolioId && !isNaN(parseInt(globalPortfolioId))) {
        initializeKeyPortfolioMetrics(globalPortfolioId);
        initializeMonteCarloAnalysis(globalPortfolioId); // Assuming MC might also use global ID if specific one isn't found
        initializeTreasuryYieldCurveDisplay(globalPortfolioId); // For the 3m, 2y, etc. display
    } else {
        console.error("DOMContentLoaded: Global Portfolio ID is missing or invalid. Some features may not initialize correctly.");
        // Handle fallback for sections that absolutely need portfolioId
        setAllKeyMetricsToPlaceholder("Portfolio ID Missing");
        const mcCardCanvas = document.getElementById("monteCarloChart");
        if (mcCardCanvas) displayChartMessage(mcCardCanvas, "Portfolio ID Missing");
        const treasuryYieldContainer = document.getElementById("treasury-yield-container"); // Assuming this ID for the curve display
        if (treasuryYieldContainer) treasuryYieldContainer.innerHTML = '<p class="text-muted">Portfolio ID missing.</p>';
    }

    // These might not strictly need a portfolio ID for their container setup,
    // but their data fetching inside will fail if their respective data-url isn't set.
    initializeNewsFeed();
    initializeExchangeRateDisplay();
    initializeAnalysisToolsTabs();
    initializeScrollPositionManager();
});

// ---------------------------------------------------------------------------------
// MODULE: KEY PORTFOLIO METRICS
// ---------------------------------------------------------------------------------

function initializeKeyPortfolioMetrics(portfolioId) {
    const refreshButton = document.getElementById("load-all-key-metrics-btn");
    const keyMetricsContainer = document.getElementById("key-metrics");

    if (!keyMetricsContainer) {
        console.warn("Key Metrics: Container 'key-metrics' not found.");
        return;
    }

    // No need for separate portfolioId check here, as it's done in DOMContentLoaded
    if (refreshButton) {
        refreshButton.addEventListener("click", () => {
            fetchAllKeyMetricsAndDisplay(portfolioId, refreshButton, false);
        });
        fetchAllKeyMetricsAndDisplay(portfolioId, refreshButton, true); // Initial load
    } else {
        // If button is missing but container exists, still try an initial load
        fetchAllKeyMetricsAndDisplay(portfolioId, null, true);
    }
}

function setAllKeyMetricsToPlaceholder(message = "N/A") {
    const metricElementIds = [
        "total-buying-price-value", "current-market-value-value", "profit-loss-value",
        "cumulative-return-value", "num-holdings-value", "mean-return-value",
        "portfolio-std-dev-value", "sharpe-ratio-value", "portfolio-beta-value",
        "max-drawdown-value", "risk-free-rate-value", "historic-var-value",
        "historic-cvar-value", "mc-var-keymetric-value", "mc-cvar-keymetric-value"
    ];
    metricElementIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = message;
            element.classList.remove('positive', 'negative');
        }
    });
}

async function fetchAllKeyMetricsAndDisplay(portfolioId, buttonElement, isInitialLoad = false) {
    if (buttonElement) {
        buttonElement.disabled = true;
        buttonElement.textContent = "Loading...";
    }
    if (isInitialLoad) {
        setAllKeyMetricsToPlaceholder("Loading...");
    }

    console.log("Fetching all key metrics for portfolioId:", portfolioId);

    const fetchOperations = [
        { name: 'performance-stats', promise: fetch(`/api/portfolio/${portfolioId}/performance-stats/`).then(handleFetchResponse) },
        { name: 'historic-std_dev',  promise: fetchRiskMeasure(portfolioId, "std_dev") },
        { name: 'historic-var',      promise: fetchRiskMeasure(portfolioId, "var") },
        { name: 'historic-cvar',     promise: fetchRiskMeasure(portfolioId, "cvar") },
        { name: 'treasury-yield',    promise: fetchTreasuryYieldForKeyMetrics(portfolioId) }, // Specifically for the "Risk-Free Rate" field
        { name: 'monte-carlo-risk',  promise: fetch(`/monte-carlo-risk/${portfolioId}/`).then(handleFetchResponse) }
    ];

    const results = await Promise.allSettled(fetchOperations.map(op => op.promise));
    const metricsData = {};

    results.forEach((result, index) => {
        const operationName = fetchOperations[index].name;
        if (result.status === 'fulfilled') {
            if (result.value && result.value.error) {
                console.error(`Error in data for ${operationName}:`, result.value.error);
                metricsData[operationName] = { error: result.value.error };
            } else if (result.value === null || typeof result.value === 'undefined') {
                console.warn(`Data for ${operationName} is null or undefined from backend.`);
                metricsData[operationName] = null;
            } else {
                metricsData[operationName] = result.value;
                console.log(`Successfully fetched data for ${operationName}:`, result.value);
            }
        } else {
            console.error(`Failed to fetch ${operationName}:`, result.reason);
            metricsData[operationName] = { error: result.reason.message || "Fetch failed" };
        }
    });

    // --- Update UI elements AFTER all promises have settled ---
    const perfStats = metricsData['performance-stats'];
    if (perfStats && !perfStats.error) {
        updateMetricDisplay("total-buying-price-value", perfStats.total_buying_price, { type: 'currency' }, 'perfStats.total_buying_price');
        updateMetricDisplay("current-market-value-value", perfStats.current_market_value, { type: 'currency' }, 'perfStats.current_market_value');
        updateMetricDisplay("num-holdings-value", perfStats.number_of_holdings, { precision: 0 }, 'perfStats.number_of_holdings');
        updateMetricDisplay("sharpe-ratio-value", perfStats.sharpe_ratio, { precision: 3 }, 'perfStats.sharpe_ratio');
        updateMetricDisplay("portfolio-beta-value", perfStats.beta, { precision: 3 }, 'perfStats.beta');
        updateMetricDisplay("max-drawdown-value", perfStats.max_drawdown_pct, { type: 'percentage', precision: 2 }, 'perfStats.max_drawdown_pct');
        updateMetricDisplay("cumulative-return-value", perfStats.cumulative_return_pct, { type: 'percentage', precision: 2, showSign: true }, 'perfStats.cumulative_return_pct');

        const buyingPrice = parseFloat(perfStats.total_buying_price);
        const currentValue = parseFloat(perfStats.current_market_value);
        if (!isNaN(buyingPrice) && !isNaN(currentValue)) {
            updateMetricDisplay("profit-loss-value", currentValue - buyingPrice, { type: 'currency', showSign: true }, 'profit-loss calculation');
        } else {
            updateMetricDisplay("profit-loss-value", null, {}, 'profit-loss calculation');
        }
    } else {
        ["total-buying-price-value", "current-market-value-value", "profit-loss-value", "num-holdings-value",
         "sharpe-ratio-value", "portfolio-beta-value", "max-drawdown-value", "cumulative-return-value"]
         .forEach(id => updateMetricDisplay(id, null, {}, `Fallback for ${id} due to perfStats error/absence`));
    }

    const histStdDev = metricsData['historic-std_dev'];
    updateMetricDisplay("portfolio-std-dev-value", histStdDev?.std_dev, { type: 'percentage', precision: 2 }, 'histStdDev.std_dev');

    const histVaR = metricsData['historic-var'];
    updateMetricDisplay("historic-var-value", histVaR?.var, { type: 'percentage', precision: 2, makeAbsolute: true }, 'histVaR.var');

    const histCVaR = metricsData['historic-cvar'];
    updateMetricDisplay("historic-cvar-value", histCVaR?.cvar, { type: 'percentage', precision: 2, makeAbsolute: true }, 'histCVaR.cvar');

    // Update Risk-Free Rate using the fetched treasury yield data
    // Assuming fetchTreasuryYieldForKeyMetrics returns an object like { yield: 0.045 } or { "10y": 4.5 }
    const treasuryForKeyMetrics = metricsData['treasury-yield'];
    if (treasuryForKeyMetrics && !treasuryForKeyMetrics.error) {
        // Prioritize '10y' if available and numeric, else 'yield', else null
        let rateValue = null;
        if (typeof treasuryForKeyMetrics["10y"] === 'number') {
            rateValue = treasuryForKeyMetrics["10y"]; // Expects 4.5 for 4.5%
        } else if (typeof treasuryForKeyMetrics.yield === 'number') {
            rateValue = treasuryForKeyMetrics.yield; // Expects 0.045 for 4.5%
        }
        updateMetricDisplay("risk-free-rate-value", rateValue, { type: 'percentage', precision: 2 }, 'treasury.yield or 10y');
    } else {
        updateMetricDisplay("risk-free-rate-value", null, {}, 'Fallback for risk-free-rate-value');
    }

    const mcRisk = metricsData['monte-carlo-risk'];
    if (mcRisk && !mcRisk.error) {
        updateMetricDisplay("mean-return-value", mcRisk.mean_return_pct, { type: 'percentage', precision: 2 }, 'mcRisk.mean_return_pct');
        updateMetricDisplay("mc-var-keymetric-value", mcRisk.VaR_pct, { type: 'percentage', precision: 2, makeAbsolute: true }, 'mcRisk.VaR_pct');
        updateMetricDisplay("mc-cvar-keymetric-value", mcRisk.CVaR_pct, { type: 'percentage', precision: 2, makeAbsolute: true }, 'mcRisk.CVaR_pct');
    } else {
        ["mean-return-value", "mc-var-keymetric-value", "mc-cvar-keymetric-value"]
        .forEach(id => updateMetricDisplay(id, null, {}, `Fallback for ${id} due to mcRisk error/absence`));
    }

    if (buttonElement) {
        buttonElement.disabled = false;
        buttonElement.textContent = "Refresh All Metrics";
    }

    const chartRiskValues = {
        std_dev: histStdDev?.std_dev,
        var: histVaR?.var,
        cvar: histCVaR?.cvar,
        treasury_yield: (typeof treasuryForKeyMetrics?.["10y"] === 'number') ? (treasuryForKeyMetrics["10y"]/100) : treasuryForKeyMetrics?.yield // Ensure decimal for chart
    };
    if (typeof renderRiskBarChart === "function") {
        renderRiskBarChart(chartRiskValues);
    }
}

async function handleFetchResponse(response) {
    if (!response.ok) {
        let errorMsg = `HTTP error ${response.status}: ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMsg = errorData?.error || errorData?.message || errorMsg;
        } catch (e) { /* Ignore */ }
        console.error(`Fetch error for ${response.url}: ${errorMsg}`);
        throw new Error(errorMsg);
    }
    try {
        const data = await response.json();
        if (data && typeof data.error !== 'undefined') {
            console.error(`Application error in response from ${response.url}:`, data.error);
            return { error: data.error }; // Let Promise.allSettled handle this structure
        }
        return data;
    } catch (e) {
        console.error(`JSON parsing error for ${response.url}:`, e);
        throw new Error(`Invalid JSON response from ${response.url}`);
    }
}

async function fetchRiskMeasure(portfolioId, measureName) {
    console.log(`Fetching risk measure: ${measureName} for portfolioId: ${portfolioId}`);
    return fetch(`/load-risk-measure/${portfolioId}/${measureName}/`).then(handleFetchResponse);
}

// Fetches general treasury yield, typically 10-year for risk-free rate in key metrics.
async function fetchTreasuryYieldForKeyMetrics(portfolioId) {
    console.log(`Fetching treasury yield (for Key Metrics Risk-Free Rate) for portfolioId: ${portfolioId}`);
    // This endpoint should ideally return the specific yield used for risk-free rate calculations,
    // e.g., { "yield": 0.045 } or { "10y": 4.5 } if it's 10-year yield directly as percentage points.
    return fetch(`/fetch-treasury-yield/${portfolioId}/`).then(handleFetchResponse);
}

function updateMetricDisplay(elementId, value, options = {}, valueSourceName = 'unknown') {
    const element = document.getElementById(elementId);
    if (!element) {
        console.warn(`Display: Element '${elementId}' not found.`);
        return;
    }

    const defaults = { precision: 2, type: 'number', currencySymbol: '$', makeAbsolute: false, showSign: false };
    const config = { ...defaults, ...options };

    element.classList.remove('positive', 'negative');

    if (value === null || typeof value === 'undefined' || (typeof value === 'number' && isNaN(value))) {
        element.textContent = "N/A";
        return;
    }
    if (typeof value === 'string' && ["n/a", "loading...", "error", "portfolio id missing"].includes(value.toLowerCase())) {
        element.textContent = value;
        return;
    }

    let numericValue = parseFloat(value);
    if (isNaN(numericValue)) {
        element.textContent = "N/A";
        return;
    }

    const originalSign = Math.sign(numericValue);
    if (config.makeAbsolute) numericValue = Math.abs(numericValue);

    let formattedValue;
    if (config.type === 'percentage') {
        let displayPercent = numericValue;
        // If valueSourceName indicates it's pre-scaled (e.g. from `_pct` field that sends 10.5 for 10.5%)
        // OR if the value is already large (e.g. > 1, suggesting it's 10 not 0.10)
        // then use it as is. Otherwise, assume it's a decimal (0.10) and multiply by 100.
        if (valueSourceName.toLowerCase().includes('_pct') || (Math.abs(numericValue) >= 1 && numericValue !==0) || valueSourceName === 'treasury.yield or 10y' && Math.abs(numericValue) >=1 ) {
            // Value is already in percentage points (e.g., 18.00 for 18%)
            // Or it's the 10y treasury yield coming as, e.g. 4.5 for 4.5%
             console.log(`   Percentage for '${elementId}' (source: ${valueSourceName}, value: ${value}): Using as percentage points: ${displayPercent}`);
        } else if (numericValue !== 0) { // It's a decimal like 0.05, needs scaling
            displayPercent = numericValue * 100;
            console.log(`   Percentage for '${elementId}' (source: ${valueSourceName}, value: ${value}): Scaled decimal ${numericValue} to ${displayPercent}`);
        }
        formattedValue = displayPercent.toFixed(config.precision) + "%";
    } else if (config.type === 'currency') {
        formattedValue = `${config.currencySymbol}${numericValue.toFixed(config.precision).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
    } else {
        formattedValue = numericValue.toFixed(config.precision);
    }

    if (config.showSign && originalSign > 0 && !formattedValue.startsWith('+')) {
        formattedValue = `+${formattedValue}`;
    }
    element.textContent = formattedValue;

    if (config.type === 'currency' || config.type === 'percentage' || config.showSign) {
        if (originalSign > 0) element.classList.add('positive');
        else if (originalSign < 0) element.classList.add('negative');
    }
}

// ---------------------------------------------------------------------------------
// MODULE: TREASURY YIELD CURVE DISPLAY (for 3m, 2y, 5y etc.)
// ---------------------------------------------------------------------------------
function initializeTreasuryYieldCurveDisplay(portfolioId) {
    const yieldContainer = document.getElementById("treasury-yield-container"); // Ensure this ID exists in your HTML for this section
    if (!yieldContainer) {
        console.warn("Treasury Yield Curve: Container 'treasury-yield-container' not found.");
        return;
    }
    // The portfolioId check is already done by the caller (DOMContentLoaded)
    fetchAndDisplayTreasuryYieldCurve(portfolioId, yieldContainer);
}

async function fetchAndDisplayTreasuryYieldCurve(portfolioId, containerElement) {
    try {
        // This endpoint should return all necessary yields, e.g., { "3m": 5.1, "2y": 4.8, ... }
        // Or if it's nested like { "yields": { "3m": ... } }, adjust data access.
        const response = await fetch(`/all-yield-data/${portfolioId}/`);
        const data = await handleFetchResponse(response); // Use consistent error handling

        if (data.error) { // Check for application-level error passed by handleFetchResponse
            console.error("Failed to load treasury yields for curve:", data.error);
            containerElement.innerHTML = `<p class="text-muted">Failed to load treasury yields: ${data.error}</p>`;
            return;
        }

        // Assuming data is directly like { "3m": 5.1, "2y": 4.8 } or a nested `data.yields`
        const yields = data.yields || data; // Adjust if data structure is different

        // Helper to update individual yield elements
        const updateYieldElement = (id, value) => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = (typeof value === 'number') ? value.toFixed(2) + "%" : "--";
            } else {
                console.warn(`Treasury Yield Curve: Element with ID '${id}' not found.`);
            }
        };

        updateYieldElement("yield-3m", yields["3m"]);
        updateYieldElement("yield-2y", yields["2y"]);
        updateYieldElement("yield-5y", yields["5y"]);
        updateYieldElement("yield-7y", yields["7y"]);
        updateYieldElement("yield-10y", yields["10y"]);
        updateYieldElement("yield-30y", yields["30y"]);

    } catch (error) { // Catches network errors or errors thrown by handleFetchResponse
        console.error("Error loading treasury yields for curve:", error);
        containerElement.innerHTML = `<p class="text-muted">Error loading treasury yields: ${error.message}</p>`;
    }
}


// ---------------------------------------------------------------------------------
// MODULE: NEWS FEED
// ---------------------------------------------------------------------------------
function initializeNewsFeed() {
    const newsContainer = document.getElementById("news-container");
    const newsDataUrl = newsContainer?.getAttribute("data-url");
    if (!newsContainer) return;
    if (!newsDataUrl) {
        newsContainer.innerHTML = "<p class='text-muted'>News feed URL not configured.</p>";
        return;
    }
    fetchAndRenderNews(newsDataUrl, newsContainer);
}
async function fetchAndRenderNews(url, container) {
    try {
        const response = await fetch(url); // Not using handleFetchResponse here if it has different error needs
        if (!response.ok) throw new Error(`HTTP error news: ${response.status}`);
        const data = await response.json();
        container.innerHTML = "";
        if (!data.news?.length) {
            container.innerHTML = "<p class='text-muted'>No news available.</p>";
            return;
        }
        data.news.forEach(article => container.appendChild(createNewsArticleElement(article)));
    } catch (error) {
        console.error("Error fetching/rendering news:", error);
        container.innerHTML = "<p class='text-muted'>Failed to load news.</p>";
    }
}
function createNewsArticleElement(article) {
    const div = document.createElement("div");
    div.classList.add("news-item");
    div.innerHTML = `<p style="margin-bottom: 4px;"><a href="${encodeURI(article.url)}" target="_blank" rel="noopener noreferrer" style="color: var(--text-link); text-decoration: none;">${article.title}</a></p><p class="text-muted" style="font-size: 0.85em;">${article.source}</p><hr style="border: 0.5px solid var(--border-light);">`;
    return div;
}

// ---------------------------------------------------------------------------------
// MODULE: EXCHANGE RATE DISPLAY
// ---------------------------------------------------------------------------------
function initializeExchangeRateDisplay() {
    const exchangeContainer = document.getElementById("exchange-rate-container");
    const exchangeDataUrl = exchangeContainer?.getAttribute("data-url");
    if (!exchangeContainer) return;
    if (!exchangeDataUrl) {
        exchangeContainer.innerHTML = "<p class='text-muted'>Exchange rate URL not configured.</p>";
        return;
    }
    fetchAndRenderExchangeRates(exchangeDataUrl, exchangeContainer);
}
async function fetchAndRenderExchangeRates(url, container) {
    try {
        const response = await fetch(url); // Not using handleFetchResponse here if it has different error needs
        if (!response.ok) throw new Error(`HTTP error exchange: ${response.status}`);
        const data = await response.json();
        container.innerHTML = "";
        if (!data.exchange_rates?.length) {
            container.innerHTML = "<p class='text-muted'>No exchange rate data.</p>";
            return;
        }
        data.exchange_rates.forEach(rateInfo => container.appendChild(createExchangeRateElement(rateInfo)));
    } catch (error) {
        console.error("Error fetching/rendering exchange rates:", error);
        container.innerHTML = "<p class='text-muted'>Failed to load exchange rates.</p>";
    }
}
function createExchangeRateElement(rateInfo) {
    const div = document.createElement("div");
    div.classList.add("exchange-rate-item");
    const rateValue = parseFloat(rateInfo.rate);
    div.innerHTML = `<p style="margin-bottom: 2px;">${rateInfo.from} → ${rateInfo.to}</p><p style="font-size: 1.2em;">${!isNaN(rateValue) ? rateValue.toFixed(4) : 'N/A'}</p><hr style="border: 0.5px solid var(--border-light);">`;
    return div;
}

// ---------------------------------------------------------------------------------
// MODULE: MONTE CARLO ANALYSIS & CHART (for dedicated MC card)
// ---------------------------------------------------------------------------------
let monteCarloChartInstance = null;
function initializeMonteCarloAnalysis(globalPortfolioIdFallback) {
    const varElem = document.getElementById("monte-carlo-var");
    const cvarElem = document.getElementById("monte-carlo-cvar");
    const meanElem = document.getElementById("monte-carlo-mean");
    const stddevElem = document.getElementById("monte-carlo-stddev");
    const chartCanvas = document.getElementById("monteCarloChart");
    const monteCarloContainer = document.querySelector("[data-montecarlo-id]");
    // Use specific ID if available, otherwise fallback to global (if passed and valid)
    const portfolioIdMC = monteCarloContainer?.dataset?.montecarloId || globalPortfolioIdFallback;

    if (!portfolioIdMC) {
        console.error("MC Card: Portfolio ID missing for Monte Carlo analysis.");
        if (chartCanvas) displayChartMessage(chartCanvas, "Portfolio ID Missing");
        [varElem, cvarElem, meanElem, stddevElem].forEach(el => { if(el) el.textContent = "N/A"; });
        return;
    }
    if (!varElem || !cvarElem || !meanElem || !stddevElem || !chartCanvas) {
        console.error("MC Card: Essential DOM elements missing for Monte Carlo display.");
        if (chartCanvas) displayChartMessage(chartCanvas, "DOM Elements Missing");
        return;
    }
    fetchAndRenderMonteCarloData(portfolioIdMC, { varElem, cvarElem, meanElem, stddevElem, chartCanvas });
}
async function fetchAndRenderMonteCarloData(portfolioId, dom) {
    try {
        const data = await fetch(`/monte-carlo-risk/${portfolioId}/`).then(handleFetchResponse);
        if (data.error) throw new Error(data.error); // Check for app-level error from handleFetchResponse

        dom.varElem.textContent = data.VaR_pct !== null ? `${Math.abs(data.VaR_pct).toFixed(2)}%` : "N/A";
        dom.cvarElem.textContent = data.CVaR_pct !== null ? `${Math.abs(data.CVaR_pct).toFixed(2)}%` : "N/A";
        dom.meanElem.textContent = data.mean_return_pct !== null ? `${data.mean_return_pct.toFixed(2)}%` : "N/A";
        dom.stddevElem.textContent = data.std_dev_return_pct !== null ? `${data.std_dev_return_pct.toFixed(2)}%` : "N/A";

        if (data.mean_return_pct === null || data.std_dev_return_pct === null || data.std_dev_return_pct === 0) {
            displayChartMessage(dom.chartCanvas, "Not enough data for chart.");
            if (monteCarloChartInstance) { monteCarloChartInstance.destroy(); monteCarloChartInstance = null; }
            return;
        }
        renderMonteCarloDistributionChart(data, dom.chartCanvas);
    } catch (err) { // Catches network errors or errors thrown by handleFetchResponse
        console.error("Error MC data for card:", err);
        [dom.varElem, dom.cvarElem, dom.meanElem, dom.stddevElem].forEach(el => {if(el) el.textContent = "Error"});
        if(dom.chartCanvas) displayChartMessage(dom.chartCanvas, err.message || "Error loading chart.");
        if (monteCarloChartInstance) { monteCarloChartInstance.destroy(); monteCarloChartInstance = null; }
    }
}
function renderMonteCarloDistributionChart(chartData, canvas) {
    const { mean_return_pct, std_dev_return_pct, VaR_pct, CVaR_pct } = chartData;
    const rangeMultiplier = 4, numPoints = 200;
    const minX = mean_return_pct - rangeMultiplier * std_dev_return_pct;
    const maxX = mean_return_pct + rangeMultiplier * std_dev_return_pct;
    const xVal = [], yVal = [];
    for (let i = 0; i <= numPoints; i++) {
        const x = minX + (i / numPoints) * (maxX - minX);
        xVal.push(x); yVal.push(gaussianPDF(x, mean_return_pct, std_dev_return_pct));
    }
    if (monteCarloChartInstance) monteCarloChartInstance.destroy();
    const ctx = canvas.getContext('2d');
    const theme = {
        link: getComputedStyle(document.documentElement).getPropertyValue('--text-link').trim() || 'blue',
        secondary: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() || 'grey',
        border: getComputedStyle(document.documentElement).getPropertyValue('--border-light').trim() || '#e0e0e0',
        red: getComputedStyle(document.documentElement).getPropertyValue('--accent-red').trim() || 'red',
        green: getComputedStyle(document.documentElement).getPropertyValue('--accent-green').trim() || 'green',
    };
    monteCarloChartInstance = new Chart(ctx, {
        type: 'line', data: { labels: xVal.map(x => x.toFixed(2)), datasets: [{ label: 'Return Distribution', data: yVal, borderColor: theme.link, borderWidth: 2, fill: {target:'origin', above:'rgba(88,166,255,0.1)'}, pointRadius:0, tension:0.4 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { title:{display:true,text:'Portfolio Daily Return (%)',color:theme.secondary}, ticks:{color:theme.secondary}, grid:{color:theme.border, drawOnChartArea:false}}, y: { title:{display:true,text:'Probability Density',color:theme.secondary}, ticks:{color:theme.secondary, precision:0}, grid:{color:theme.border}}},
        plugins: { legend:{display:false}, tooltip:{enabled:true, mode:'index', intersect:false}, annotation:{annotations:{
            varLine:VaR_pct!==null?{type:'line',xMin:VaR_pct,xMax:VaR_pct,borderColor:theme.red,borderWidth:2,borderDash:[6,6],label:{content:`VaR: ${Math.abs(VaR_pct).toFixed(2)}%`,enabled:true,position:'start',backgroundColor:'rgba(0,0,0,0.7)',color:'white',yAdjust:-15}}:{},
            cvarLine:CVaR_pct!==null?{type:'line',xMin:CVaR_pct,xMax:CVaR_pct,borderColor:theme.red,borderWidth:2,label:{content:`CVaR: ${Math.abs(CVaR_pct).toFixed(2)}%`,enabled:true,position:'end',backgroundColor:'rgba(0,0,0,0.7)',color:'white',yAdjust:15}}:{},
            meanLine:mean_return_pct!==null?{type:'line',xMin:mean_return_pct,xMax:mean_return_pct,borderColor:theme.green,borderWidth:1.5,borderDash:[3,3],label:{content:`Mean: ${mean_return_pct.toFixed(2)}%`,enabled:true,position:'center',backgroundColor:'rgba(0,0,0,0.7)',color:'white',yAdjust:-30}}:{},
            varTailArea:VaR_pct!==null?{type:'box',xMin:minX,xMax:VaR_pct,backgroundColor:'rgba(255,146,146,0.15)',borderColor:'transparent'}:{}
        }}}}
    });
}
function gaussianPDF(x, mean, stdDev) { if (stdDev === 0) return x === mean ? Infinity : 0; return (1/(stdDev*Math.sqrt(2*Math.PI)))*Math.exp(-0.5*Math.pow((x-mean)/stdDev,2)); }
function displayChartMessage(canvas, msg) { if (!canvas) return; const ctx=canvas.getContext('2d'); ctx.clearRect(0,0,canvas.width,canvas.height); ctx.font="16px Inter, sans-serif"; ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim()||'#6c757d'; ctx.textAlign="center"; ctx.fillText(msg,canvas.width/2,canvas.height/2 > 50 ? canvas.height/2 : 50); }

// ---------------------------------------------------------------------------------
// MODULE: ANALYSIS TOOLS TABS
// ---------------------------------------------------------------------------------
function initializeAnalysisToolsTabs() {
    const hub = document.getElementById('analysis-tools-hub');
    if (!hub) return;
    const links = hub.querySelectorAll('.tabs-nav .tab-link');
    const panes = hub.querySelectorAll('.tabs-content .tab-pane');
    if (!links.length || !panes.length) return;
    links.forEach(link => link.addEventListener('click', function(e){ e.preventDefault(); handleTabClick(this,links,panes,hub); }));
}
function handleTabClick(clicked, allLinks, allPanes, hub) {
    const targetId='tab-'+clicked.dataset.tab;
    allLinks.forEach(l=>l.classList.remove('active'));
    allPanes.forEach(p=>p.classList.remove('active'));
    clicked.classList.add('active');
    const targetPane=hub.querySelector('#'+targetId);
    if(targetPane) targetPane.classList.add('active');
}

// ---------------------------------------------------------------------------------
// MODULE: SCROLL POSITION MANAGER
// ---------------------------------------------------------------------------------
function initializeScrollPositionManager() { window.addEventListener("beforeunload",storeScrollPosition); window.addEventListener("load",restoreScrollPosition); }
function storeScrollPosition() { sessionStorage.setItem("portfolioDashboardScrollPos",window.scrollY.toString()); }
function restoreScrollPosition() { const pos=sessionStorage.getItem("portfolioDashboardScrollPos"); if(pos!==null) window.scrollTo(0,parseInt(pos,10)); }

// --- End of Script ---