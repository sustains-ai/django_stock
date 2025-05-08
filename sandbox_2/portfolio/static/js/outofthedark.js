document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".cards-container");
    if (!container) {
        console.error("❌ .cards-container not found");
        return;
    }

    // Create cursor light
    const cursorLight = document.createElement("div");
    cursorLight.className = "cursor-light";
    document.body.appendChild(cursorLight);

    document.addEventListener("mousemove", (e) => {
        cursorLight.style.left = `${e.clientX}px`;
        cursorLight.style.top = `${e.clientY}px`;
    });

    // Fetch market status
    fetch("/api/market-status/")
        .then(res => res.json())
        .then(data => {
            const markets = data.markets || [];
            console.log("✅ Markets received:", markets);

            // Create two sets of cards for seamless looping
            for (let i = 0; i < 2; i++) {
                markets.forEach((market, j) => {
                    const card = document.createElement("div");
                    card.className = "card";

                    const glowColor = market.current_status === "open" ? "#0ABF53" : "#DC2626";
                    card.style.setProperty("--glow-color", glowColor);
                    card.style.setProperty("--glow-duration", `${3 + Math.random() * 3}s`);
                    card.style.setProperty("--glow-delay", `${Math.random() * -5}s`);

                    card.innerHTML = `
                        <div class="card-content" style="padding: 1rem; color: white; text-align: center;">
                            <h4>${market.region}</h4>
                            <p>Status: <strong>${market.current_status}</strong></p>
                            <p style="font-size: 0.85rem;">${market.primary_exchanges || "N/A"}</p>
                            <p style="font-size: 0.75rem; opacity: 0.7;">${market.notes || ""}</p>
                        </div>
                    `;

                    container.appendChild(card);
                });
            }

            if (markets.length === 0) {
                console.warn("⚠️ No markets found in API response.");
                return;
            }

            // Infinite vertical scroll animation
            let scrollPosition = 0;
            const scrollSpeed = 0.5; // Adjust speed as needed
            const totalHeight = container.scrollHeight / 2; // Half the height since we duplicated the cards

            function animate() {
                scrollPosition += scrollSpeed;
                if (scrollPosition >= totalHeight) {
                    scrollPosition = 0; // Reset to top for infinite loop
                }
                container.style.transform = `translateY(-${scrollPosition}px)`;
                requestAnimationFrame(animate);
            }

            animate();
        })
        .catch(err => {
            console.error("❌ Error fetching market status:", err);
        });
});