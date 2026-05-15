/* Simple canvas bar/line chart for the comparison page.
   Relies on chartData global injected by compare.html. */

(function () {
  const canvas = document.getElementById("compareChart");
  if (!canvas || !window.chartData) return;
  const ctx = canvas.getContext("2d");

  const data   = chartData.filter(d => d.bank_rate !== null);
  const years  = data.map(d => d.year);
  const inf    = data.map(d => d.inflation);
  const br     = data.map(d => d.bank_rate);
  const real   = data.map(d => d.real_rate);

  const W = canvas.width;
  const H = canvas.height;
  const padL = 48, padR = 20, padT = 30, padB = 50;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;

  const allVals = [...inf, ...br, ...real];
  const minY = Math.floor(Math.min(...allVals)) - 1;
  const maxY = Math.ceil(Math.max(...allVals)) + 1;
  const rangeY = maxY - minY;

  function xPos(i) { return padL + (i / (years.length - 1)) * chartW; }
  function yPos(v) { return padT + chartH - ((v - minY) / rangeY) * chartH; }

  // Grid lines
  ctx.strokeStyle = "#dce3ea";
  ctx.lineWidth = 1;
  for (let v = Math.ceil(minY); v <= maxY; v += 2) {
    const y = yPos(v);
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillStyle = "#7f8c8d"; ctx.font = "11px Segoe UI, Arial";
    ctx.textAlign = "right"; ctx.fillText(v + "%", padL - 5, y + 4);
  }

  // Zero line
  if (minY < 0) {
    ctx.strokeStyle = "#999"; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(padL, yPos(0)); ctx.lineTo(W - padR, yPos(0)); ctx.stroke();
  }

  function drawLine(vals, color, width, dash) {
    ctx.strokeStyle = color; ctx.lineWidth = width;
    ctx.setLineDash(dash || []);
    ctx.beginPath();
    vals.forEach((v, i) => {
      const x = xPos(i), y = yPos(v);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }

  drawLine(inf,  "#e67e22", 2.5);
  drawLine(br,   "#1a3a5c", 2.5);
  drawLine(real, "#27ae60", 1.8, [5, 4]);

  // X axis labels (every 5 years)
  ctx.fillStyle = "#2c3e50"; ctx.font = "11px Segoe UI, Arial";
  ctx.textAlign = "center";
  years.forEach((yr, i) => {
    if (yr % 5 === 0) {
      ctx.fillText(yr, xPos(i), H - padB + 18);
    }
  });

  // Legend
  const legend = [
    { label: "CPI Inflation", color: "#e67e22", dash: false },
    { label: "Bank Rate (approx. avg)", color: "#1a3a5c", dash: false },
    { label: "Real Rate", color: "#27ae60", dash: true },
  ];
  let lx = padL;
  legend.forEach(item => {
    ctx.strokeStyle = item.color; ctx.lineWidth = 2;
    ctx.setLineDash(item.dash ? [5, 4] : []);
    ctx.beginPath(); ctx.moveTo(lx, padT - 12); ctx.lineTo(lx + 28, padT - 12); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#2c3e50"; ctx.font = "12px Segoe UI, Arial"; ctx.textAlign = "left";
    ctx.fillText(item.label, lx + 32, padT - 8);
    lx += 180;
  });
})();
