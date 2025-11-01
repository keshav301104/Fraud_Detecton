document.addEventListener("DOMContentLoaded", () => {
    
    // --- Page/Tab Elements ---
    const pageDashboard = document.getElementById("page-dashboard");
    const pageModeler = document.getElementById("page-modeler");
    const btnDashboard = document.getElementById("btn-dashboard");
    const btnModeler = document.getElementById("btn-modeler");

    // --- Initial Load ---
    loadDashboardStats(); // Load global stats for dashboard page
    fetchRecentTransactions(); // Load recent tx for modeler page
    pageDashboard.classList.add("active"); // Show dashboard by default

    // --- Navigation Logic ---
    btnDashboard.addEventListener("click", () => {
        pageDashboard.classList.add("active");
        pageModeler.classList.remove("active");
        btnDashboard.classList.add("active");
        btnModeler.classList.remove("active");
    });

    btnModeler.addEventListener("click", () => {
        pageDashboard.classList.remove("active");
        pageModeler.classList.add("active");
        btnDashboard.classList.remove("active");
        btnModeler.classList.add("active");
    });

    // --- Modeler Form Logic ---
    const predictForm = document.getElementById("predict-form");
    predictForm.addEventListener("submit", handlePrediction);
});

/**
 * NEW: Loads all stats for the Global Dashboard page
 */
function loadDashboardStats() {
    fetch('/get-global-stats')
        .then(response => response.json())
        .then(stats => {
            if (stats.error) throw new Error(stats.error);

            // 1. Populate KPI Cards
            document.getElementById('kpi-total-tx').innerText = stats.kpis.total_transactions.toLocaleString();
            document.getElementById('kpi-total-volume').innerText = Math.round(stats.kpis.total_volume).toLocaleString('en-IN');
            document.getElementById('kpi-total-fraud').innerText = stats.kpis.total_fraud.toLocaleString();
            document.getElementById('kpi-fraud-rate').innerText = `${stats.kpis.fraud_rate.toFixed(4)}%`;

            // 2. Draw Transaction Type Pie Chart
            const typeCtx = document.getElementById('type-pie-chart').getContext('2d');
            new Chart(typeCtx, {
                type: 'pie',
                data: {
                    labels: stats.charts.type_chart.labels,
                    datasets: [{
                        label: 'Transaction Types',
                        data: stats.charts.type_chart.data,
                        backgroundColor: ['#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ae2012'],
                        hoverOffset: 4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
            });

            // 3. Draw Fraud vs. Safe Doughnut Chart
            const fraudCtx = document.getElementById('fraud-doughnut-chart').getContext('2d');
            new Chart(fraudCtx, {
                type: 'doughnut',
                data: {
                    labels: stats.charts.fraud_chart.labels,
                    datasets: [{
                        label: 'Transaction Status',
                        data: stats.charts.fraud_chart.data,
                        backgroundColor: ['#2d6a4f', '#9b2226'],
                        hoverOffset: 4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
            });

        })
        .catch(error => {
            console.error('Error loading global stats:', error);
            // You could show an error on the dashboard page
        });
}

/**
 * Fetches the last 20 transactions (from sample) for the Modeler page.
 */
function fetchRecentTransactions() {
    const tableBody = document.getElementById("transactions-table-body");
    tableBody.innerHTML = '<tr><td colspan="6">Loading transactions...</td></tr>'; 

    fetch('/get-recent-transactions')
        .then(response => response.json())
        .then(data => {
            tableBody.innerHTML = ""; 
            data.forEach(tx => {
                const row = document.createElement("tr");
                if (tx.isFraud === 1) { row.classList.add("fraud-row"); }
                row.innerHTML = `
                    <td>${tx.Transaction_ID}</td>
                    <td>${tx.type}</td>
                    <td>${tx.amount.toFixed(2)}</td>
                    <td>${tx.Sender_ID}</td>
                    <td>${tx.Receiver_ID}</td>
                    <td>${tx.isFraud === 1 ? 'Yes' : 'No'}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error("Error fetching transactions:", error);
            tableBody.innerHTML = '<tr><td colspan="6">Error loading transactions.</td></tr>';
        });
}

/**
 * Handles the submission of the fraud prediction form.
 */
function handlePrediction(event) {
    event.preventDefault(); 
    const form = event.target;
    const sender_id = form.elements.sender_id.value;
    const receiver_id = form.elements.receiver_id.value;
    const type = form.elements.type.value;
    const amount = form.elements.amount.value;
    const resultMessageDiv = document.getElementById("result-message");

    resultMessageDiv.textContent = "Checking...";
    resultMessageDiv.className = "result";
    resultMessageDiv.style.display = "block";

    fetch('/predict-fraud', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sender_id: sender_id,
            receiver_id: receiver_id,
            type: type,
            amount: amount
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) { throw new Error(data.error); }
        const riskPercent = (data.risk_score * 100).toFixed(2);
        if (data.is_fraud === 1) {
            resultMessageDiv.textContent = `DANGER! This transaction is ${riskPercent}% likely to be fraud.`;
            resultMessageDiv.className = "result result-danger";
        } else {
            resultMessageDiv.textContent = `This transaction appears safe (${riskPercent}% risk).`;
            resultMessageDiv.className = "result result-safe";
        }
    })
    .catch(error => {
        console.error("Error during prediction:", error);
        resultMessageDiv.textContent = "Error checking transaction.";
        resultMessageDiv.className = "result result-danger";
    });
}