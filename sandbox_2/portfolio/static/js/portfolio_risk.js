document.addEventListener("DOMContentLoaded", function() {
    console.log("portfolio_risk.js loaded");  // Debugging to check if the script runs

    document.getElementById("load-risk-btn").addEventListener("click", function() {
        let measure = document.getElementById("risk-selector").value;
        let portfolioId = document.getElementById("risk-selector").dataset.portfolioId;
        let riskContent = document.getElementById("risk-content");

        // Show loading message
        riskContent.innerHTML = "<p class='text-center text-muted'>Loading...</p>";

        fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    riskContent.innerHTML = `<p class='text-danger'>Error: ${data.error}</p>`;
                } else {
                    riskContent.innerHTML = `<p class='text-success'>${measure.toUpperCase()}: ${data[measure]}</p>`;
                }
            })
            .catch(error => {
                riskContent.innerHTML = "<p class='text-danger'>Failed to load data.</p>";
                console.error("Error loading risk measure:", error);
            });
    });
});


document.addEventListener("DOMContentLoaded", function() {
    // Get the canvas element for the pie chart
    const pieCanvas = document.getElementById("portfolioChart_advanced");

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
