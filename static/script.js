const chart = document.getElementsByClassName("chart");
for (const el of chart) {
  const config = JSON.parse(el.getAttribute("config").replace(/'/g, '"'));
  new Chart(el, config);
}

const new_chart = document.getElementsByClassName("new_chart");

function getPairs() {
  return [...document.querySelectorAll('#new_chart_data_rows div')].map(row => {
    const [l, v] = row.querySelectorAll('input');
    return { label: l.value, value: v.value };
  });
}

function newLiveChart() {
  const pairs = getPairs();
  live_chart = new Chart(new_chart, {
    type: document.getElementById('chart_type').value,
    data: {
      labels: pairs.map(p => p.label),
      datasets: [{
        label: document.getElementById('caption').value,
        data: pairs.map(p => parseFloat(p.value))
      }]
    }
  });
}

function updateChart() {
  const pairs = getPairs();
  if (typeof live_chart != 'undefined') {
    if (live_chart.type != document.getElementById('chart_type').value) {
      live_chart.destroy();
      newLiveChart();
    }
    live_chart.data.labels = pairs.map(p => p.label);
    live_chart.data.datasets[0].label = document.getElementById('caption').value;
    live_chart.data.datasets[0].data = pairs.map(p => parseFloat(p.value));
    live_chart.update();

  } else {
    newLiveChart();
  }
}

updateChart();

function addRow(l='', v='') {
  const div = document.createElement('div');
  div.innerHTML = `
    <input type="text" placeholder="Label" value="${l}">
    <input type="number" placeholder="Value" value="${v}">
    <button onclick="this.parentElement.remove(); updateChart()">✕</button>
  `;
  document.getElementById('new_chart_data_rows').appendChild(div);
}

function serializeAndSubmit(e) {
  e.preventDefault();
  const pairs = getPairs();
  document.getElementById('new_chart_data').value = JSON.stringify(pairs);
  e.target.submit();
}

