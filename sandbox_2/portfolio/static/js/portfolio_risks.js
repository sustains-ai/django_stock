document.addEventListener("DOMContentLoaded", () => {
    // initializeGraphs(); // This was already moved into the other DOMContentLoaded listener
    // fetchAndDisplayRiskMeasures(); // This will be called below

    const loadAllRisksButton = document.getElementById("load-all-risks-btn"); // Renamed for clarity
    const portfolioContainer = document.getElementById("portfolio-container"); // Renamed for clarity
    const portfolioId = portfolioContainer?.dataset?.portfolioId;

    if (loadAllRisksButton && portfolioId) {
        loadAllRisksButton.addEventListener("click", () => {
            // Disable button to prevent multiple clicks while fetching
            loadAllRisksButton.disabled = true;
            loadAllRisksButton.textContent = "Loading..."; // Provide user feedback

            const measures = ["std_dev", "var", "cvar"];
            const riskValues = {};

            Promise.all(measures.map(measure =>
                fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
                    .then(response => { // Renamed for clarity
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status} for ${measure}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        riskValues[measure] = data[measure]; // Assuming the backend returns { "measure_name": value }
                    })
                    .catch(error => {
                        console.error(`Error fetching ${measure}:`, error);
                        riskValues[measure] = null; // Or some default error indicator
                        // Optionally update the specific cell with an error message here
                    })
            ))
            .then(() => {
                // Update text content
                document.getElementById("variance-value").textContent = typeof riskValues.std_dev === 'number' ? riskValues.std_dev.toFixed(5) : "N/A";
                document.getElementById("var-value").textContent = typeof riskValues.var === 'number' ? riskValues.var.toFixed(5) : "N/A";
                document.getElementById("cvar-value").textContent = typeof riskValues.cvar === 'number' ? riskValues.cvar.toFixed(5) : "N/A";

                // The renderRiskBarChart function already uses the new color palette
                renderRiskBarChart(riskValues);
            })
            .finally(() => {
                // Re-enable button and reset text
                loadAllRisksButton.disabled = false;
                loadAllRisksButton.textContent = "Load All Risk Measures"; // Or original text
            });
        });
    } else {
        if (!loadAllRisksButton) console.warn("Button with ID 'load-all-risks-btn' not found.");
        if (!portfolioId) console.warn("Portfolio ID not found in 'portfolio-container' dataset.");
    }

    // Initial fetch of risk measures when the page loads
    fetchAndDisplayRiskMeasures();
});

function fetchAndDisplayRiskMeasures() {
    const portfolioContainer = document.getElementById("portfolio-container"); // Renamed for clarity
    const portfolioId = portfolioContainer?.dataset?.portfolioId;

    if (!portfolioId) {
        // console.warn("Portfolio ID not found for initial risk measure fetch."); // Already logged by button logic if applicable
        // Set default text for cells if no portfolioId
        const defaultText = "N/A";
        document.getElementById("variance-value").textContent = defaultText;
        document.getElementById("var-value").textContent = defaultText;
        document.getElementById("cvar-value").textContent = defaultText;
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
        if (cell) cell.textContent = "Loading..."; // Initial loading state

        fetch(`/load-risk-measure/${portfolioId}/${measure}/`)
            .then(response => { // Renamed for clarity
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} for ${measure}`);
                }
                return response.json();
            })
            .then(data => {
                if (cell) {
                    if (data && typeof data[measure] === 'number') { // Check if data and data[measure] exist and is a number
                        cell.textContent = parseFloat(data[measure]).toFixed(4);
                        // **Potential for dynamic coloring based on value here**
                        // Example:
                        // if (measure === 'var' && data[measure] > SOME_THRESHOLD) {
                        //    cell.style.color = '#DA3633'; // High Risk Red
                        // } else {
                        //    cell.style.color = ''; // Reset to default CSS color
                        // }
                    } else {
                        cell.textContent = "N/A"; // Data not available or not a number
                        console.warn(`Data for ${measure} not found or invalid in response:`, data);
                    }
                }
            })
            .catch(error => {
                console.error(`Error fetching initial ${measure}:`, error);
                if (cell) cell.textContent = "Error"; // Display error in the cell
            });
    });
}

// In your main JS file or the script tag in analyze_portfolio.html

function initializeSidebar() {
    // ... (sidebar open/close logic) ...
    // ... (sidebar link active state logic) ...
}

