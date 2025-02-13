function getRandomColor() {
    return `rgba(${Math.floor(Math.random() * 255)}, 
                 ${Math.floor(Math.random() * 255)}, 
                 ${Math.floor(Math.random() * 255)}, 
                 1)`;
}




document.addEventListener("DOMContentLoaded", function() {
    // Get the canvas element for the pie chart
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
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)'
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
});









document.addEventListener("DOMContentLoaded", function () {
    const stockChartElement = document.getElementById("stockChart");

    if (stockChartElement) {
        console.log("Raw Data:", stockChartElement.dataset.historical);

        try {
            const historicalData = JSON.parse(stockChartElement.dataset.historical);

            console.log("Parsed historical data:", historicalData);

            if (Object.keys(historicalData).length === 0) {
                console.warn("No historical data available.");
                return;
            }

            const labels = historicalData[Object.keys(historicalData)[0]].dates; // Get dates
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
});
