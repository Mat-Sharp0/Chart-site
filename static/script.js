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
const charts = document.querySelectorAll(".chart");

charts.forEach(el => {
  const config = JSON.parse(el.dataset.config);

  if (!config.options) config.options = {};

  config.options.responsive = true;
  config.options.maintainAspectRatio = false;

  if (!config.options.scales) config.options.scales = {};
  if (!config.options.scales.y) config.options.scales.y = {};

  config.options.scales.y.ticks = {
    callback: (value) => numbro(value).format({ average: true, totalLength: 4, trimMantissa: true, mantissa: 2}).toUpperCase()
  };

  if (!config.options.plugins) config.options.plugins = {};
  if (!config.options.plugins.tooltip) config.options.plugins.tooltip = {};
  
  config.options.plugins.tooltip.callbacks = {
    label: (context) => `${context.dataset.label} : ${numbro(context.parsed.y).format({ average: true, totalLength: 4, trimMantissa: true, mantissa: 2 }).toUpperCase()}`
  };

  new Chart(el, config);
});



const chartCanvas = document.querySelector(".new_chart");

if (chartCanvas) {
  let live_chart = null;

  function getPairs() {
    return [...document.querySelectorAll('#new_chart_data_rows div')].map(row => {
      const [l, v] = row.querySelectorAll('input');
      return { label: l.value, value: v.value };
    });
  }

  function updateChart() {
    const pairs = getPairs();
    const chartType = document.getElementById('chart_type').value;
    const caption = document.getElementById('caption').value;
    
    const labels = pairs.map(p => p.label);
    const data = pairs.map(p => numbro.unformat(p.value.toLowerCase().replace(',', '.').replace(/\s/g, '')) || 0);

    if (live_chart) {
      if (live_chart.config.type !== chartType) {
        live_chart.destroy();
        live_chart = null;
      } else {
        live_chart.data.labels = labels;
        live_chart.data.datasets[0].label = caption;
        live_chart.data.datasets[0].data = data;
        live_chart.update();
        return;
      }
    }

    live_chart = new Chart(chartCanvas, {
      type: chartType,
      data: {
        labels: labels,
        datasets: [{ label: caption, data: data }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: {
              callback: (value) => numbro(value).format({ average: true, totalLength: 4, trimMantissa: true, mantissa: 2}).toUpperCase()
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => `${context.dataset.label} : ${numbro(context.parsed.y).format({ average: true, totalLength: 4, trimMantissa: true, mantissa: 2 }).toUpperCase()}`
            }
          }
        }
      }
    });
  }

  function addRow(l='', v='') {
    const div = document.createElement('div');
    div.innerHTML = `
      <input type="text" placeholder="Label" value="${l}">
      <input type="text" placeholder="Value" value="${v}">
      <button onclick="this.parentElement.remove(); updateChart()">✕</button>
    `;
    document.getElementById('new_chart_data_rows').appendChild(div);
  }

  function serializeAndSubmit(e) {
    e.preventDefault();
    document.getElementById('new_chart_data').value = JSON.stringify(getPairs());
    e.target.submit();
  }

  updateChart();
}


function openReportModal() {
  document.getElementById("reportModal").style.display = "block";
}
function closeReportModal() {
  document.getElementById("reportModal").style.display = "none";
}
