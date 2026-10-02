// SAE Risk Trend Chart

const riskCanvas = document.getElementById("riskChart");

new Chart(riskCanvas, {
    type: "line",

    data: {
        labels: [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun"
        ],

        datasets: [
            {
                label: "High Risk",
                data: [18, 21, 19, 25, 27, 30, 32],
                borderWidth: 3,
                tension: 0.4,
                fill: false
            },
            {
                label: "Medium Risk",
                data: [32, 35, 34, 38, 40, 39, 42],
                borderWidth: 2,
                tension: 0.4,
                fill: false
            }
        ]
    },

    options: {
        responsive: true,

        plugins: {
            legend: {
                position: "bottom"
            }
        }
    }
});


// Risk Distribution Chart

const distributionCanvas =
    document.getElementById("distributionChart");

new Chart(distributionCanvas, {

    type: "doughnut",

    data: {

        labels: [
            "Low Risk",
            "Medium Risk",
            "High Risk"
        ],

        datasets: [
            {
                data: [149, 67, 32],
                borderWidth: 0
            }
        ]
    },

    options: {

        responsive: true,

        cutout: "68%",

        plugins: {
            legend: {
                position: "bottom"
            }
        }
    }
});