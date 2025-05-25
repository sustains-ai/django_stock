function initializeGraphs() {
    if (typeof Plotly === "undefined") {
        console.warn("Plotly library not found."); // Added a warning
        return;
    }
    renderPortfolioValueChart();
    // Consider if resizePortfolioChart is still needed with CSS flex/grid for layout
    // If the chart container itself is responsive, Plotly might handle it.
    // If you still need it, ensure it works well with the new layout.
    window.addEventListener("resize", resizePortfolioChart);
}

function renderPortfolioValueChart() {
    const container = document.getElementById("portfolio-container");
    // Using optional chaining and nullish coalescing for safety
    const dataString = container?.dataset?.portfolioValue ?? "[]";
    let data;
    try {
        data = JSON.parse(dataString);
    } catch (e) {
        console.error("Failed to parse portfolio value data:", e);
        data = [];
    }

    if (!data.length) {
        // Optionally, display a message in the chart div if no data
        // const chartDiv = document.getElementById("portfolio-valueoveryears-chart");
        // if (chartDiv) chartDiv.innerHTML = "<p style='text-align:center; color: #8B949E;'>No portfolio value data to display.</p>";
        return;
    }

    const trace = {
        x: data.map(d => d.x),
        y: data.map(d => d.y),
        mode: "lines",
        name: "Portfolio Value",
        line: { color: "#3081F7" } // Primary Accent Blue (or #2DA44E for Green)
    };

    const layout = {
        // title: "Portfolio Value Over Time", // Title can be an H3 tag in HTML for better semantics
        title: {
            text: "Portfolio Value Over Time",
            font: {
                color: "#CDD9E5", // Primary Text
                size: 18 // Optional: adjust size
            }
        },
        xaxis: {
            title: {
                text: "Date",
                font: { color: "#8B949E" } // Secondary Text for axis titles
            },
            tickfont: { color: "#8B949E" }, // Secondary Text for tick labels
            gridcolor: "#30363D",       // Borders/Dividers for grid lines
            linecolor: "#30363D"        // Borders/Dividers for axis line
        },
        yaxis: {
            title: {
                text: "Value",
                font: { color: "#8B949E" } // Secondary Text
            },
            tickfont: { color: "#8B949E" }, // Secondary Text
            gridcolor: "#30363D",       // Borders/Dividers
            linecolor: "#30363D"        // Borders/Dividers
        },
        plot_bgcolor: "rgba(0,0,0,0)",  // Transparent, to show section background
        paper_bgcolor: "rgba(0,0,0,0)", // Transparent
        autosize: true, // Let Plotly try to autosize
        margin: { // Adjust margins if title or labels get cut off
            l: 60, // left
            r: 30, // right
            b: 50, // bottom
            t: 50, // top (increase if title is long)
            pad: 4
        },
        legend: {
            font: {
                color: "#CDD9E5" // Primary text for legend
            }
        }
    };
    // Ensure the target div exists
    const chartDiv = document.getElementById("portfolio-valueoveryears-chart");
    if (chartDiv) {
        Plotly.newPlot(chartDiv, [trace], layout, {responsive: true}); // Added responsive config
    } else {
        console.warn("Chart container 'portfolio-valueoveryears-chart' not found.");
    }
}

function resizePortfolioChart() {
    // Plotly's {responsive: true} config in newPlot should handle most cases.
    // This manual resize might still be useful for specific scenarios or if
    // the parent container's resize isn't directly tracked by Plotly's default.
    const chartDiv = document.getElementById("portfolio-valueoveryears-chart");
    if (chartDiv && chartDiv.classList.contains('js-plotly-plot')) { // Check if it's a Plotly chart
        Plotly.Plots.resize(chartDiv);
    }
}

// Assuming this function is called somewhere with appropriate data
function renderRiskBarChart(riskData) { // Renamed parameter for clarity
    if (!riskData || Object.keys(riskData).length === 0) {
        // const chartDiv = document.getElementById("all-risk-chart");
        // if (chartDiv) chartDiv.innerHTML = "<p style='text-align:center; color: #8B949E;'>No risk data to display.</p>";
        return;
    }

    const trace = {
        x: Object.keys(riskData).map(key => key.toUpperCase()),
        y: Object.values(riskData),
        type: "bar",
        marker: {
            color: "#3081F7", // Primary Accent Blue (or #2DA44E for Green)
            // You could also have an array of colors if each bar should be different:
            // color: ['#DA3633', '#DBAB09', '#2DA44E', '#3081F7'] // Example: Red, Amber, Green, Blue
        }
    };

    const layout = {
        // title: "Portfolio Risk Measures",
        title: {
            text: "Portfolio Risk Measures",
            font: {
                color: "#CDD9E5", // Primary Text
                size: 18
            }
        },
        xaxis: {
            title: {
                text: "Risk Measure",
                font: { color: "#8B949E" } // Secondary Text
            },
            tickfont: { color: "#8B949E" } // Secondary Text
            // No grid/line color needed for x-axis in typical bar charts, but can be added
        },
        yaxis: {
            title: {
                text: "Value",
                font: { color: "#8B949E" } // Secondary Text
            },
            tickfont: { color: "#8B949E" }, // Secondary Text
            gridcolor: "#30363D",       // Borders/Dividers
            linecolor: "#30363D"        // Borders/Dividers
        },
        plot_bgcolor: "rgba(0,0,0,0)",  // Transparent
        paper_bgcolor: "rgba(0,0,0,0)", // Transparent
        autosize: true,
        margin: { l: 60, r: 30, b: 50, t: 50, pad: 4 },
        bargap: 0.2 // Optional: adjust gap between bars
    };

    const chartDiv = document.getElementById("all-risk-chart");
    if (chartDiv) {
        Plotly.newPlot(chartDiv, [trace], layout, {responsive: true});
    } else {
        console.warn("Chart container 'all-risk-chart' not found.");
    }
}


// The sidebar JavaScript remains unchanged as it doesn't directly handle colors.
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const pageContent = document.querySelector('.page-content-area');

    if (sidebar) {
        sidebar.addEventListener('click', function(event) {
            if (event.target.tagName === 'A' && sidebar.classList.contains('sidebar-is-open')) {
                return;
            }

            const sidebarRect = sidebar.getBoundingClientRect();
            // Refined handle click: only if closed, and click is within the visible part
            const isHandleAreaClick = !sidebar.classList.contains('sidebar-is-open') &&
                                   event.clientX >= sidebarRect.left &&
                                   event.clientX <= sidebarRect.right; // entire visible part

            if (sidebar.classList.contains('sidebar-is-open') || isHandleAreaClick ) {
                 sidebar.classList.toggle('sidebar-is-open');
            }
            // Removed the more complex `else if` as the above should cover it.
            // If the sidebar is closed, any click on its visible area (handle) should toggle it.
        });

        if (pageContent) {
            pageContent.addEventListener('click', function() {
                if (sidebar.classList.contains('sidebar-is-open')) {
                    sidebar.classList.remove('sidebar-is-open');
                }
            });
        }
    } else {
        // Conditional warning for sidebar
        if (document.querySelector('.sidebar-layout')) { // Only warn if a sidebar layout is expected
            console.warn('Sidebar element (.sidebar) not found within .sidebar-layout.');
        }
    }

    // Call initializeGraphs after DOM is ready and sidebar logic is set up
    initializeGraphs();
});