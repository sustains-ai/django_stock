function fetchESGScores(portfolioId) {
    const spinner = document.getElementById("loading-spinner");
    const tableBody = document.getElementById("esg-scores-body");
    const table = document.getElementById("esg-table");
    const noDataDiv = document.getElementById("no-data-message");

    tableBody.innerHTML = "";
    noDataDiv.textContent = "";
    spinner.style.display = "block"; // Show spinner
    table.style.display = "none";

    fetch(`/fetch-esg-scores/${portfolioId}/`)
        .then(response => response.json())
        .then(data => {
            spinner.style.display = "none"; // Hide spinner

            if (!data.esg_scores || data.esg_scores.length === 0) {
                noDataDiv.textContent = "No ESG scores available. Data will be updated soon.";
                return;
            }

            table.style.display = "table";

            data.esg_scores.forEach(row => {
                const tr = document.createElement("tr");
                row.forEach(cell => {
                    const td = document.createElement("td");
                    td.textContent = cell;
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });
        })
        .catch(error => {
            spinner.style.display = "none"; // Hide spinner
            console.error("Error fetching ESG scores:", error);
        });
}
