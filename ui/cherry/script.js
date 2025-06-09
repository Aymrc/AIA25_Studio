fetch("http://127.0.0.1:5001/api/gwp_data")
  .then(res => res.json())
  .then(data => {
    const gallery = document.getElementById("gallery");

    data
      .sort((a, b) => {
        const numA = parseInt(a.version.replace("V", ""));
        const numB = parseInt(b.version.replace("V", ""));
        return numA - numB;
      })
      .forEach(item => {
        const tile = document.createElement("div");
        tile.className = "viz-tile";

        const label = document.createElement("div");
        label.className = "viz-label";
        label.innerText = item.version;

        const img = new Image();
        img.src = `http://127.0.0.1:5001/static/iterations/${item.version}.png`;
        img.onload = () => {
          tile.appendChild(img);
          tile.appendChild(label);
        };
        img.onerror = () => {
          tile.classList.add("no-image");
          tile.appendChild(label);
        };

        gallery.appendChild(tile);
      });
  });
