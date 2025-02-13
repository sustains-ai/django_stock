document.addEventListener("DOMContentLoaded", function() {
    const stockChartCanvas = document.getElementById("stockChart");

    if (stockChartCanvas) {
        // Extract historical data from data attribute
        const historicalData = JSON.parse(stockChartCanvas.dataset.historical);

        // Prepare datasets for Chart.js
        const datasets = Object.keys(historicalData).map(symbol => ({
            label: symbol,
            data: historicalData[symbol].prices,
            borderColor: getRandomColor(), // Function for random colors
            fill: false
        }));

        // Create the Line Chart
        new Chart(stockChartCanvas.getContext("2d"), {
            type: "line",
            data: {
                labels: historicalData[Object.keys(historicalData)[0]].dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" }
                },
                scales: {
                    x: { title: { display: true, text: "Date" } },
                    y: { title: { display: true, text: "Price (Adjusted Close)" } }
                }
            }
        });

        // Function to generate a random color
        function getRandomColor() {
            return `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 1)`;
        }
    }
});
