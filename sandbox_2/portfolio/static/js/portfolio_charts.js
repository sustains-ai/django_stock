// REMOVE or comment out old color functions and palettes:
// function getRandomColor() { ... }
// const gradientPalette = [ ... ];
// function getRandomColors(length) { ... } // We're replacing this with getChartColors

// New palette for charts, derived from the B2B scheme
const chartColorPalette = [
    "#FF5733", "#54AA63", "#E231E2", "#800567", "#111169",
    "#800522", "#78CDE2", "#FA02F2", "#FF00FF", "#FA0202",
    "#FA7A02", "#053E80", "#028FFA", "#FF007F", "#54E578",
    "#020EFA", "#B802FA", "#0E4A0F", "#FA027E", "#FA0227",
    "#379C16", "#05806D", "#13579B", "#260580", "#9BCE24",
    "#8C0A1B"
]

// ✅ Use colors from the new palette cyclically
function getChartColors(length) {
    return Array.from({ length }, (_, i) => chartColorPalette[i % chartColorPalette.length]);
}

// Function to get a single color from the palette (useful for single lines or specific elements)
function getSingleChartColor(index = 0) {
    return chartColorPalette[index % chartColorPalette.length];
}


function parseDataAttribute(element, attribute) {
    if (!element) { // Added check for element existence
        console.warn(`Element not found for parsing attribute: ${attribute}`);
        return {};
    }
    try {
        // Use optional chaining for dataset access
        const dataString = element.dataset?.[attribute];
        if (dataString === undefined) {
            // console.warn(`Data attribute '${attribute}' not found on element.`); // Can be noisy
            return {};
        }
        return JSON.parse(dataString);
    } catch (error) {
        console.error(`Error parsing attribute '${attribute}' from element:`, element, error);
        return {};
    }
}

function createPieChart(canvasId, data, label) {
    const chartElement = document.getElementById(canvasId);
    if (!chartElement) {
        console.warn(`Canvas element with ID '${canvasId}' not found.`);
        return;
    }
    if (Object.keys(data).length === 0) {
        // console.warn(`No data provided for pie chart: ${label}`); // Can be noisy
        // Optionally display a message in the canvas
        // chartElement.getContext("2d").fillText("No data to display.", 10, 50);
        return;
    }

    new Chart(chartElement.getContext("2d"), {
        type: "pie",
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: getChartColors(Object.keys(data).length), // USE NEW PALETTE
                borderColor: '#161B22', // Secondary Background (or card bg #1F242C) for segment borders
                borderWidth: 1 // Optional: adds a slight separation
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: '#CDD9E5' // Primary Text for legend labels
                    }
                },
                title: {
                    display: true,
                    text: label,
                    color: '#CDD9E5', // Primary Text for chart title
                    font: {
                        size: 16 // Optional: adjust font size
                    }
                },
                tooltip: {
                    bodyFont: { size: 12 },
                    titleFont: { size: 14 },
                    // backgroundColor: 'rgba(0,0,0,0.7)', // Default is usually fine
                    // titleColor: '#FFFFFF',
                    // bodyColor: '#FFFFFF'
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const pieCanvas = document.getElementById("portfolioChart");
    if (pieCanvas) {
        const pieCtx = pieCanvas.getContext("2d");
        let stockLabels = [];
        let stockValues = [];
        try {
            stockLabels = JSON.parse(pieCanvas.dataset.labels || "[]");
            stockValues = JSON.parse(pieCanvas.dataset.values || "[]");
        } catch (e) {
            console.error("Error parsing portfolioChart data attributes:", e);
        }


        if (stockLabels.length > 0 && stockValues.length > 0) {
            new Chart(pieCtx, {
                type: "pie",
                data: {
                    labels: stockLabels,
                    datasets: [{
                        data: stockValues,
                        backgroundColor: getChartColors(stockLabels.length), // USE NEW PALETTE
                        borderColor: '#161B22',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#CDD9E5' // Primary Text
                            }
                        },
                        title: { // Added title for consistency
                            display: true,
                            text: 'Portfolio Distribution', // Or get from a data attribute if dynamic
                            color: '#CDD9E5',
                            font: { size: 16 }
                        }
                    }
                }
            });
        } else {
            // console.warn("No data for portfolioChart.");
        }
    }

    const stockChartElement = document.getElementById("stockChart");
    if (stockChartElement) {
        try {
            const historicalDataString = stockChartElement.dataset.historical;
            if (!historicalDataString) {
                // console.warn("Historical data attribute not found for stockChart.");
                return;
            }
            const historicalData = JSON.parse(historicalDataString);
            if (Object.keys(historicalData).length === 0) {
                // console.warn("No historical data available for stockChart.");
                return;
            }

            // Ensure there's at least one stock's data to get dates from
            const firstStockSymbol = Object.keys(historicalData)[0];
            if (!historicalData[firstStockSymbol] || !historicalData[firstStockSymbol].dates) {
                console.error("Historical data format error: missing dates for the first stock.");
                return;
            }
            const labels = historicalData[firstStockSymbol].dates;

            // Use getChartColors for multiple lines, ensuring distinct colors
            const lineColors = getChartColors(Object.keys(historicalData).length);
            const datasets = Object.keys(historicalData).map((symbol, index) => ({
                label: symbol,
                data: historicalData[symbol].prices,
                borderColor: lineColors[index], // USE NEW PALETTE (cyclically)
                backgroundColor: lineColors[index] + '33', // Lighter version with alpha for area fill if desired
                fill: false, // Set to 'origin' or true for area under line
                tension: 0.1 // Makes lines a bit smoother
            }));

            new Chart(stockChartElement.getContext("2d"), {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#CDD9E5' // Primary Text
                            }
                        },
                        title: {
                            display: true,
                            text: 'Stock Price Fluctuations',
                            color: '#CDD9E5',
                            font: { size: 16 }
                        },
                        tooltip: {
                            mode: 'index', // Show tooltip for all datasets at that x-index
                            intersect: false,
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date',
                                color: '#8B949E' // Secondary Text
                            },
                            ticks: {
                                color: '#8B949E' // Secondary Text
                            },
                            grid: {
                                color: '#30363D' // Borders/Dividers
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Price', // Removed (Adjusted Close) for brevity unless essential
                                color: '#8B949E' // Secondary Text
                            },
                            ticks: {
                                color: '#8B949E', // Secondary Text
                                // beginAtZero: false // Default, adjust if needed
                            },
                            grid: {
                                color: '#30363D' // Borders/Dividers
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error processing or rendering stockChart:", error);
        }
    }

    // These calls will now use the updated createPieChart function with the new palette
    createPieChart("mvPieChart", parseDataAttribute(document.getElementById("mvPieChart"), "mv"), "Mean-Variance Allocation");
    createPieChart("cvarPieChart", parseDataAttribute(document.getElementById("cvarPieChart"), "cvar"), "CVaR Allocation");
    createPieChart("ercPieChart", parseDataAttribute(document.getElementById("ercPieChart"), "erc"), "ERC Allocation");
});


document.addEventListener("DOMContentLoaded", function () {
    const chartCanvas = document.getElementById("treasuryYieldChart");
    const portfolioContainer = document.getElementById("portfolio-container");
    const portfolioId = portfolioContainer?.dataset?.portfolioId;

    if (chartCanvas && portfolioId) {
        fetch(`/fetch-treasury-yield/${portfolioId}/`)
            .then(response => response.json())
            .then(data => {
                if (!data.labels || !data.values) {
                    chartCanvas.parentElement.innerHTML += "<p class='text-muted'>No yield data available.</p>";
                    return;
                }

                new Chart(chartCanvas, {
                    type: "line",
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: "10-Year US Treasury Yield (%)",
                            data: data.values,
                            borderWidth: 2,
                            fill: false,
                            tension: 0.2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: false,
                                title: {
                                    display: true,
                                    text: "Yield (%)"
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: "Date"
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: true,
                                position: "top"
                            }
                        }
                    }
                });
            })
            .catch(() => {
                chartCanvas.parentElement.innerHTML += "<p class='text-muted'>Failed to load chart data.</p>";
            });
    }
});
