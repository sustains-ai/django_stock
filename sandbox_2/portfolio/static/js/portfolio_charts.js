function getRandomColor() {
    return `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 1)`;
}

// 🎨 Gradient color palette (9 colors cycling)
const gradientPalette = [
    'rgba(245, 204, 232, 0.8)',  // #F5CCE8
    'rgba(240, 180, 224, 0.8)',
    'rgba(236, 157, 237, 0.8)',  // #EC9DED
    'rgba(215, 135, 223, 0.8)',
    'rgba(200, 128, 183, 0.8)',  // #C880B7
    'rgba(171, 112, 164, 0.8)',
    'rgba(159, 107, 160, 0.8)',  // #9F6BA0
    'rgba(100, 60, 100, 0.8)',
    'rgba(74, 32, 64, 0.8)'      // #4A2040
];

// ✅ Use colors from palette cyclically
function getRandomColors(length) {
    return Array.from({ length }, (_, i) => gradientPalette[i % gradientPalette.length]);
}






function parseDataAttribute(element, attribute) {
    try {
        return JSON.parse(element.dataset[attribute]);
    } catch (error) {
        console.error(`Error parsing ${attribute}:`, error);
        return {};
    }
}

function createPieChart(canvasId, data, label) {
    const chartElement = document.getElementById(canvasId);
    if (!chartElement || Object.keys(data).length === 0) return;

    new Chart(chartElement.getContext("2d"), {
        type: "pie",
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: getRandomColors(Object.keys(data).length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom" },
                title: { display: true, text: label }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const pieCanvas = document.getElementById("portfolioChart");
    if (pieCanvas) {
        const pieCtx = pieCanvas.getContext("2d");
        const stockLabels = JSON.parse(pieCanvas.dataset.labels);
        const stockValues = JSON.parse(pieCanvas.dataset.values);

        new Chart(pieCtx, {
            type: "pie",
            data: {
                labels: stockLabels,
                datasets: [{
                    data: stockValues,
                    backgroundColor: getRandomColors(stockLabels.length)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    const stockChartElement = document.getElementById("stockChart");
    if (stockChartElement) {
        try {
            const historicalData = JSON.parse(stockChartElement.dataset.historical);
            const labels = historicalData[Object.keys(historicalData)[0]].dates;
            const datasets = Object.keys(historicalData).map(symbol => ({
                label: symbol,
                data: historicalData[symbol].prices,
                borderColor: getRandomColor(),
                fill: false
            }));

            new Chart(stockChartElement.getContext("2d"), {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                    scales: {
                        x: { title: { display: true, text: 'Date' } },
                        y: { title: { display: true, text: 'Price (Adjusted Close)' } }
                    }
                }
            });
        } catch (error) {
            console.error("Error parsing historicalData:", error);
        }
    }

    createPieChart("mvPieChart", parseDataAttribute(document.getElementById("mvPieChart"), "mv"), "Mean-Variance Allocation");
    createPieChart("cvarPieChart", parseDataAttribute(document.getElementById("cvarPieChart"), "cvar"), "CVaR Allocation");
    createPieChart("ercPieChart", parseDataAttribute(document.getElementById("ercPieChart"), "erc"), "Equal Risk Contribution (ERC) Allocation");
});
