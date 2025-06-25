let selected = [];

function handleTileClick(tile) {
  const id = tile.dataset.id;

  if (!id) return;

  if (selected.includes(id)) {
    selected = selected.filter(sel => sel !== id);
  } else {
    if (selected.length < 2) {
      selected.push(id);
    } else {
      selected.shift();
      selected.push(id);
    }
  }

  updateTileVisuals();
  updateComparePanel();
}

function updateTileVisuals() {
  document.querySelectorAll('.tile').forEach(tile => {
    const id = tile.dataset.id;
    tile.classList.toggle('selected', selected.includes(id));
  });
}

function updateComparePanel() {
  const panel = document.getElementById('comparePanel');
  const singlePanel = document.getElementById('singlePanel');
  const singleDetails = document.getElementById('singleDetails');
  const plotDiv = document.getElementById('radarPlot');
  const comparisonTable = document.getElementById('comparisonTable');

  if (selected.length === 1) {
    // === Show single variant panel ===
    const id = selected[0];
    panel.classList.remove('active');
    plotDiv.innerHTML = '';
    comparisonTable.innerHTML = '';
    singlePanel.classList.add('active');

    fetch(`/knowledge/iterations/${id}.json`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch JSON");
        return res.json();
      })
      .then(data => {
        const metrics = [
          "Energy Intensity - EUI (kWh/m²a)",
          "Cooling Demand (kWh/m²a)",
          "Heating Demand (kWh/m²a)",
          "Operational Carbon (kg CO2e/m²a GFA)",
          "Embodied Carbon A1-A3 (kg CO2e/m²a GFA)",
          "Embodied Carbon A-D (kg CO2e/m²a GFA)",
          "GWP total (kg CO2e/m²a GFA)"
        ];

        let html = `
        <table class="comparison-table-inner">
          <thead>
            <tr><th>Metric</th><th>Value</th></tr>
          </thead>
          <tbody>`;

        metrics.forEach(metric => {
          const val = data.outputs?.[metric];
          html += `<tr>
            <td>${metric}</td>
            <td>${val?.toFixed(2) ?? "n/a"}</td>
          </tr>`;
        });

        html += "</tbody></table>";
        singleDetails.innerHTML = html;
      })
      .catch(err => {
        console.error("Error fetching single variant data:", err);
        singlePanel.classList.remove('active');
      });

  } else if (selected.length === 2) {
    // === Show comparison panel ===
    singlePanel.classList.remove('active');
    singleDetails.innerHTML = '';
    panel.classList.add('active');

    Promise.all(selected.map(id =>
      fetch(`/knowledge/iterations/${id}.json`)
        .then(res => {
          if (!res.ok) throw new Error(`Failed to fetch ${id}`);
          return res.json();
        })
    )).then(([data1, data2]) => {
      const metrics = [
        "Energy Intensity - EUI (kWh/m²a)",
        "Cooling Demand (kWh/m²a)",
        "Heating Demand (kWh/m²a)",
        "Operational Carbon (kg CO2e/m²a GFA)",
        "Embodied Carbon A1-A3 (kg CO2e/m²a GFA)",
        "Embodied Carbon A-D (kg CO2e/m²a GFA)",
        "GWP total (kg CO2e/m²a GFA)"
      ];

      let tableHTML = `<table class="comparison-table-inner"><thead><tr>
        <th>Metric</th>
        <th>${selected[0]}</th>
        <th>${selected[1]}</th>
      </tr></thead><tbody>`;

      metrics.forEach(metric => {
        const v1 = data1.outputs[metric]?.toFixed(2) ?? "n/a";
        const v2 = data2.outputs[metric]?.toFixed(2) ?? "n/a";
        tableHTML += `<tr>
          <td>${metric}</td>
          <td>${v1}</td>
          <td>${v2}</td>
        </tr>`;
      });

      tableHTML += "</tbody></table>";
      comparisonTable.innerHTML = tableHTML;

      const trace1 = {
        type: 'scatterpolar',
        r: metrics.map(m => data1.outputs[m] ?? 0),
        theta: metrics,
        fill: 'toself',
        name: selected[0]
      };

      const trace2 = {
        type: 'scatterpolar',
        r: metrics.map(m => data2.outputs[m] ?? 0),
        theta: metrics,
        fill: 'toself',
        name: selected[1]
      };

      Plotly.newPlot(plotDiv, [trace1, trace2], {
        polar: { radialaxis: { visible: true } },
        showlegend: true,
        margin: { t: 30, b: 30 }
      });

    }).catch(err => {
      console.error("Error fetching or comparing data:", err);
    });

  } else {
    // === No selection — clear both panels ===
    panel.classList.remove('active');
    comparisonTable.innerHTML = '';
    plotDiv.innerHTML = '';
    singlePanel.classList.remove('active');
    singleDetails.innerHTML = '';
  }
}






async function loadTilesFromAPI() {
  try {
    const res = await fetch('http://localhost:5001/api/gwp_data');
    const data = await res.json();

    if (!Array.isArray(data)) {
      throw new Error("Invalid data from API");
    }

    const grid = document.querySelector('.grid');

    data.forEach(item => {
      const version = item.version;
      const outputs = item.outputs || {};
      const gwp = outputs["GWP total (kg CO2e/m²a GFA)"] ?? "n/a";

      const tile = document.createElement('div');
      tile.classList.add('tile');
      tile.dataset.id = version;

      const img = document.createElement('img');
      img.src = `/images/${version}.png`;

      img.alt = version;
      img.classList.add('image-placeholder');

      const renderImgPath = `/images/${version}_render.png`;
      const defaultImgPath = `/images/${version}.png`;

      // placeholder for genAI images hover
      img.addEventListener('mouseenter', () => {
        const tempImg = new Image();
        tempImg.onload = () => {
          img.src = renderImgPath;
        };
        tempImg.onerror = () => {
          // fallback — do nothing
        };
        tempImg.src = renderImgPath;
      });

      img.addEventListener('mouseleave', () => {
        img.src = defaultImgPath;
      });

      const info = document.createElement('div');
      info.className = 'tile-info';
      info.innerHTML = `
        <h2>${version}</h2>
        <p>GWP: ${gwp}</p>
      `;

      tile.appendChild(img);
      tile.appendChild(info);
      grid.appendChild(tile);

      tile.addEventListener('click', () => handleTileClick(tile));
    });

  } catch (err) {
    console.error("Failed to load tiles from API:", err);
  }
}

// Start loading once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  loadTilesFromAPI();
});
