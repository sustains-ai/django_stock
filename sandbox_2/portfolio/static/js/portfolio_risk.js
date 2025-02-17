document.addEventListener("DOMContentLoaded", function () {
    let portfolioContainer = document.getElementById("portfolio-container");

    if (!portfolioContainer) {
        console.error("❌ Error: Portfolio container not found!");
        return;
    }

    let portfolioId = portfolioContainer.dataset.portfolioId;

    if (!portfolioId) {
        console.error("❌ Error: Portfolio ID is missing or undefined.");
        return;
    }

    console.log(`✅ Detected Portfolio ID: ${portfolioId}`);

    document.getElementById("load-risk-btn").addEventListener("click", function () {
        let measure = document.getElementById("risk-selector").value;
        let riskContent = document.getElementById("risk-content");

        // Show loading message
        riskContent.innerHTML = "<p class='text-center text-muted'>Loading...</p>";

        fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
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
