let chart = null;
let selectedHour = null;
let currentLocation = null;
let map;
let markers = [];
let lastAlert = {};

const locations = {
    "Hinjewadi": [18.5912, 73.7389],
    "Wakad": [18.5975, 73.7610],
    "Baner": [18.5590, 73.7868],
    "Shivajinagar": [18.5308, 73.8470],
    "Kothrud": [18.5074, 73.8077],
    "Swargate": [18.5010, 73.8620]
};

function initMap() {
    map = L.map('map').setView([18.5204, 73.8567], 12); // Pune

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    updateMap(); // initial load
}

function getColor(level) {
    if (level === "High") return "red";
    if (level === "Medium") return "orange";
    return "green";
}

function updateMap() {

    // clear old markers
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    let weather = document.getElementById("weather").value;
    let day = document.getElementById("day").value;

    Object.keys(locations).forEach(loc => {

        fetch(`/predict?hour=now&location=${loc}&weather=${weather}&day=${day}`)
            .then(res => res.json())
            .then(data => {

                let color = getColor(data.congestion);

                let marker = L.circleMarker(locations[loc], {
                    radius: 10,
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.8
                }).addTo(map);

                marker.bindPopup(`
                <b>${loc}</b><br>
                🚦 ${data.congestion}<br>
                🚗 ${data.vehicles}
            `);

                markers.push(marker);
            });
    });
}

function useCurrentTime() {
    selectedHour = "now";
    predict();
}

function loadChart(location) {
    fetch(`/data?location=${location}`)
        .then(res => res.json())
        .then(data => {

            console.log("Chart Data:", data); // 🔥 DEBUG

            if (!data || Object.keys(data).length === 0) {
                console.error("No data received!");
                return;
            }

            const canvas = document.getElementById("chart");
            if (!canvas) {
                console.error("Canvas not found!");
                return;
            }

            const ctx = canvas.getContext("2d"); // ✅ define first

            if (!ctx) {
                console.error("Context not found!");
                return;
            }

            // 🔥 Convert properly
            const labels = Object.keys(data).map(x => parseInt(x)).sort((a,b)=>a-b);
            const values = labels.map(h => data[h]);

            chart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: "Traffic Flow",
                            data: values,
                            borderColor: "#00c6ff",
                            backgroundColor: "rgba(0,198,255,0.2)",
                            borderWidth: 3,
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: "Prediction",
                            data: new Array(24).fill(null),
                            pointRadius: 10,
                            pointBackgroundColor: "red",
                            showLine: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: { color: "cyan" }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: "white" },
                            grid: { color: "rgba(255,255,255,0.1)" }
                        },
                        y: {
                            ticks: { color: "white" },
                            grid: { color: "rgba(255,255,255,0.1)" }
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Chart Error:", err));
}

function predict() {
    let hourInput = document.getElementById("hour").value;
    let location = document.getElementById("location").value;
    let weather = document.getElementById("weather").value;
    let day = document.getElementById("day").value;

    let hour = selectedHour === "now" ? "now" : hourInput;

    if (!hour) { alert("Enter hour"); return; }

    if (location !== currentLocation) {
        loadChart(location);
        currentLocation = location;
    }
    document.getElementById("result").innerHTML = "⏳ Loading...";

    fetch(`/predict?hour=${hour}&location=${location}&weather=${weather}&day=${day}`)
        .then(res => res.json())
        .then(data => {

            if (data.error) { alert(data.error); return; }

            let color = data.congestion === "High" ? "🔴" :
                data.congestion === "Medium" ? "🟡" : "🟢";

            let score = 100 - data.vehicles;

            document.getElementById("result").innerHTML = `
            <div class="result-card">
                <h3>📊 Traffic Insights</h3>
                <p>🕒 ${data.hour}:00</p>
                <p>🚦 ${data.congestion}</p>
                <p>🎯 ${data.confidence}%</p>
                <p>🚗 ${data.vehicles}</p>

                <p style="color:cyan;">${data.suggestion}</p>
                <p style="color:red;">${data.alert}</p>

                <p>⚠️ ${Object.keys(data.peak_hours).join(", ")}</p>
                <p>🔥 ${data.trend_peak}:00</p>
                <p>🟢 ${data.trend_low}:00</p>
                <p>✅ ${data.best_time}:00</p>
            </div>
            `;

            if (chart && chart.data && chart.data.datasets && chart.data.datasets.length > 1) {

                let predictionData = new Array(24).fill(null); // reset clean

                let hourIndex = parseInt(data.hour);

                if (!isNaN(hourIndex) && hourIndex >= 0 && hourIndex <= 23) {
                    predictionData[hourIndex] = data.vehicles;
                }

                chart.data.datasets[1].data = predictionData;

                chart.update();
            }

            selectedHour = null;
        });
}

function toggleChat() {
    let chat = document.querySelector(".chatbox");

    if (chat.style.display === "none" || chat.style.display === "") {
        chat.style.display = "block";
    } else {
        chat.style.display = "none";
    }
}

function sendMessage() {
    let input = document.getElementById("chat-input");
    let msg = input.value;

    if (!msg) return;

    let chatBox = document.getElementById("chat-messages");

    // User message
    chatBox.innerHTML += `<div>🧑: ${msg}</div>`;

    input.value = "";

    // 🤖 Typing placeholder
    let botDiv = document.createElement("div");
    botDiv.innerHTML = "🤖: <span class='dots'></span>";
    chatBox.appendChild(botDiv);

    chatBox.scrollTop = chatBox.scrollHeight;

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: msg })
    })
        .then(res => res.json())
        .then(data => {

            let text = data.reply;
            let i = 0;

            // Clear "Typing..."
            botDiv.innerHTML = "🤖: ";

            function typeEffect() {
                if (i < text.length) {
                    botDiv.innerHTML += text.charAt(i);
                    i++;
                    chatBox.scrollTop = chatBox.scrollHeight;
                    setTimeout(typeEffect, 20); // speed
                }
            }

            setTimeout(typeEffect, 400); // delay (thinking)
        });
}

function showAlert(message) {
    let box = document.getElementById("alert-box");

    let div = document.createElement("div");
    div.className = "alert";
    div.innerText = message;

    box.appendChild(div);

    setTimeout(() => {
        div.remove();
    }, 4000);
}

function checkTrafficAlerts() {

    let weather = document.getElementById("weather").value;
    let day = document.getElementById("day").value;

    Object.keys(locations).forEach(loc => {

        fetch(`/predict?hour=now&location=${loc}&weather=${weather}&day=${day}`)
        .then(res => res.json())
        .then(data => {

            if (data.congestion === "High") {

                // 🧠 prevent spam (only once per location)
                if (!lastAlert[loc]) {

                    showAlert(`🚨 Heavy traffic at ${loc}! Avoid this route.`);

                    lastAlert[loc] = true;

                    // 🔊 optional sound
                    playAlertSound();
                }

            } else {
                lastAlert[loc] = false;
            }
        });

    });
}

function playAlertSound() {
    const audio = new Audio("https://www.soundjay.com/buttons/sounds/beep-01a.mp3");
    audio.play();
}

setInterval(() => {
    updateMap();
    checkTrafficAlerts();
}, 7000);

window.onload = () => {
    let location = document.getElementById("location").value;
    loadChart(location);
    initMap();
};

console.log("Chart Data:", data);