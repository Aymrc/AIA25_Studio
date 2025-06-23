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
  const compareList = document.getElementById('compareList');
  const plotDiv = document.getElementById('radarPlot');

  if (selected.length === 2) {
    panel.classList.add('active');
    compareList.textContent = `${selected[0]} vs ${selected[1]}`;

    Promise.all(selected.map(id =>
      fetch(`/knowledge/iterations/${id}.json`).then(res => res.json())
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

      const layout = {
        polar: {
          radialaxis: { visible: true }
        },
        showlegend: true,
        margin: { t: 30, b: 30 }
      };

      Plotly.newPlot(plotDiv, [trace1, trace2], layout);
    });

  } else {
    panel.classList.remove('active');
    compareList.textContent = 'none';
    Plotly.purge(plotDiv);
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
      img.src = `/knowledge/iterations/${version}.png`;
      img.alt = version;
      img.classList.add('image-placeholder');

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
    console.error("🚨 Failed to load tiles from API:", err);
  }
}

// Start loading once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  loadTilesFromAPI();
});
