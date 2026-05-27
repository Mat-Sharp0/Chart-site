document.addEventListener("DOMContentLoaded", function() {

  // Element selection
  const form = document.querySelector("form");
  const titleFiled = document.querySelector("input[name='title']");
  const descriptionFiled = document.querySelector("textarea[name='description']");
  const sourceFiled = document.querySelector("input[name='source']");
  const overlay = document.getElementById("loading-overlay");

  // Filed validation
  function validateFiled(filed, condition, message) {
    let error = filed.parentElement.querySelector(".error-message");

    if (!condition) {
      if (!error) {
        error = document.createElement("p");
        error.classList.add("error-message");
        filed.parentElement.appendChild(error);
      }

      error.textContent = message;
      filed.classList.add("invalid-filed");
      return false;
    } else {
      if(error) error.remove();
      filed.classList.remove("invalid-filed");
      return true;
    }
    
  }

  //Real-time validation
  titleFiled.addEventListener("input", function() {
    validateFiled(titleFiled, titleFiled.value.trim().length >= 4, "The title must contain at least 4 characters.")
  });

  descriptionFiled.addEventListener("input", function() {
    validateFiled(descriptionFiled, descriptionFiled.value.trim().length >= 10, "The description must contain at least 10 characters.")
  });

  // Submit validation
  form.addEventListener("submit", function(event) {
    const titleOk = validateFiled(titleFiled, titleFiled.value.trim().length >= 4, "The title must contain at least 4 characters.")
    const descriptionOk = validateFiled(descriptionFiled, descriptionFiled.value.trim().length >= 10, "The description must contain at least 10 characters.")

    if (!titleOk || !descriptionOk) {
      event.preventDefault();
      return;
    }
    if (overlay) {
      overlay.classList.remove("hidden");

      event.preventDefault();

      setTimeout(() => {form.submit(); 10000});
    }
  });
});

if (document.getElementById('subscribe-button')) {
  document.getElementById('subscribe-button').addEventListener('click', function() {
    const targetId = this.getAttribute('target-id');
    fetch('/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ "targetId": targetId})
    })
    .then(response => response.json())
    .then(data => {
      if(data.error) {
        console.log(data.error);
      } else if(data.is_subscribe) {
        this.innerText = "Unsubscribe";
      } else {
        this.innerText = "Subscribe";
      }
    })
  });
}

// Chart display
const chart = document.getElementsByClassName("chart");
for (const el of chart) {
  const config = JSON.parse(el.getAttribute("config").replace(/'/g, '"'));
  if (!config.options) {
    config.options = {};
  }
  config.options.responsive = true;
  config.options.maintainAspectRatio = false;
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
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
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

