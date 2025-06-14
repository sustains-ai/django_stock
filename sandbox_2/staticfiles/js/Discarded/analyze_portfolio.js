function getRandomColor() {
    return `rgba(${Math.floor(Math.random() * 255)}, 
                 ${Math.floor(Math.random() * 255)}, 
                 ${Math.floor(Math.random() * 255)}, 
                 1)`;
}

function getRandomColors(length) {
    return Array.from({ length }, () =>
        `rgba(${Math.floor(Math.random() * 255)}, 
               ${Math.floor(Math.random() * 255)}, 
               ${Math.floor(Math.random() * 255)}, 
               0.7)`
    );
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
    if (!chartElement || Object.keys(data).length === 0) {
        console.warn(`No data available for ${canvasId}`);
        return;
    }

    const labels = Object.keys(data);
    const values = Object.values(data);

    new Chart(chartElement.getContext("2d"), {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: getRandomColors(labels.length) // Replace here if you want monochrome
                // backgroundColor: ['#0ABF53', '#0ABF53AA', '#0ABF5377'] // optional consistent style
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

document.addEventListener("DOMContentLoaded", function () {
    // 🎯 Portfolio Overview Pie Chart
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
                    backgroundColor: [
                        "#FF5733", "#54AA63", "#E231E2", "#800567", "#111169",
                        "#800522", "#78CDE2", "#FA02F2", "#FF00FF", "#FA0202",
                        "#FA7A02", "#053E80", "#028FFA", "#FF007F", "#54E578",
                        "#020EFA", "#B802FA", "#0E4A0F", "#FA027E", "#FA0227",
                        "#379C16", "#05806D", "#13579B", "#260580", "#9BCE24",
                        "#8C0A1B"
                    ]
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

    // 📈 Stock Price Line Chart
    const stockChartElement = document.getElementById("stockChart");
    if (stockChartElement) {
        try {
            const historicalData = JSON.parse(stockChartElement.dataset.historical);
            if (Object.keys(historicalData).length === 0) {
                console.warn("No historical data available.");
                return;
            }

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

    // 📊 Optimal Portfolio Allocation Pie Charts
    createPieChart("mvPieChart", parseDataAttribute(document.getElementById("mvPieChart"), "mv"), "Mean-Variance Allocation");
    createPieChart("cvarPieChart", parseDataAttribute(document.getElementById("cvarPieChart"), "cvar"), "CVaR Allocation");
    createPieChart("ercPieChart", parseDataAttribute(document.getElementById("ercPieChart"), "erc"), "Equal Risk Contribution (ERC) Allocation");
});
