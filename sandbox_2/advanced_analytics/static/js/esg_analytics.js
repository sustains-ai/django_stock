function fetchESGScores(portfolioId) {
    fetch(`/fetch-esg-scores/${portfolioId}/`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById("esg-scores-body");
            const table = document.getElementById("esg-table");
            const noDataDiv = document.getElementById("no-data-message");

            tableBody.innerHTML = "";
            noDataDiv.textContent = "";

            if (!data.esg_scores || data.esg_scores.length === 0) {
                table.style.display = "none";
                noDataDiv.textContent = "No ESG scores available. Data will be updated soon.";
                return;
            }

            table.style.display = "table";

            data.esg_scores.forEach(row => {
                const tr = document.createElement("tr");
                row.forEach(cell => {
                    const td = document.createElement("td");
                    td.textContent = (cell && cell.toString().trim() !== "") ? cell : "No data";
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error("Error fetching ESG scores:", error);
        });
}
