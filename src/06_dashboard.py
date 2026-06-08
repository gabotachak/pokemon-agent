"""06_dashboard.py — FastAPI dashboard en tiempo real para el entrenamiento RL

Endpoints:
  GET  /         → HTML dashboard
  GET  /metrics  → JSON lista de checkpoints
  POST /update   → agrega checkpoint
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()
checkpoints: list[dict] = []


class Checkpoint(BaseModel):
    episode: int
    win_rate: float
    avg_reward: float = 0.0
    epsilon: float = 1.0


@app.post("/update")
async def update(cp: Checkpoint):
    checkpoints.append(cp.model_dump())
    return {"ok": True, "total": len(checkpoints)}


@app.get("/metrics")
async def metrics():
    return JSONResponse(checkpoints)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pokémon RL Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #1a1a2e; color: #eee; font-family: 'Segoe UI', sans-serif; padding: 20px; }
  h1 { color: #e63946; font-size: 1.5rem; margin-bottom: 6px; }
  .subtitle { color: #888; font-size: 0.85rem; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .card { background: #16213e; border-radius: 10px; padding: 18px; border: 1px solid #0f3460; }
  .card h2 { font-size: 0.8rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
  .stat { font-size: 2rem; font-weight: bold; }
  .wr  { color: #e63946; }
  .ep  { color: #4cc9f0; }
  .eps { color: #ffd700; }
  .qs  { color: #06d6a0; }
  .chart-wrap { background: #16213e; border-radius: 10px; padding: 18px; border: 1px solid #0f3460; margin-bottom: 24px; }
  .chart-wrap h2 { font-size: 0.85rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { background: #0f3460; color: #4cc9f0; padding: 8px 10px; text-align: left; }
  td { padding: 7px 10px; border-bottom: 1px solid #1e2d4d; }
  tr:hover td { background: #1e2d4d; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 0.75rem; font-weight: bold; }
  .win  { background: #e63946; }
  .loss { background: #444; color: #aaa; }
  #status { font-size: 0.75rem; color: #555; text-align: right; margin-top: 8px; }
</style>
</head>
<body>

<h1>⚡ Pokémon RL — Training Dashboard</h1>
<p class="subtitle">gen8randombattle · Q-Learning · auto-refresh 2s</p>

<div class="grid">
  <div class="card"><h2>Win Rate (último 100)</h2><div class="stat wr" id="wr">—</div></div>
  <div class="card"><h2>Episodio</h2><div class="stat ep" id="ep">—</div></div>
  <div class="card"><h2>Epsilon</h2><div class="stat eps" id="eps">—</div></div>
  <div class="card"><h2>Checkpoints</h2><div class="stat qs" id="total">—</div></div>
</div>

<div class="chart-wrap">
  <h2>Win Rate a lo largo del entrenamiento</h2>
  <canvas id="wrChart" height="90"></canvas>
</div>

<div class="chart-wrap">
  <h2>Últimas 10 batallas</h2>
  <table>
    <thead><tr><th>Episodio</th><th>Win Rate</th><th>Epsilon</th><th>Resultado</th></tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="status">Esperando datos...</div>
</div>

<script>
const ctx = document.getElementById('wrChart').getContext('2d');
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Win Rate',
      data: [],
      borderColor: '#e63946',
      backgroundColor: 'rgba(230,57,70,0.1)',
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: true,
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { labels: { color: '#eee' } } },
    scales: {
      x: { ticks: { color: '#888' }, grid: { color: '#1e2d4d' } },
      y: { min: 0, max: 1, ticks: { color: '#888', format: { style: 'percent' } },
           grid: { color: '#1e2d4d' } }
    }
  }
});

async function refresh() {
  try {
    const data = await fetch('/metrics').then(r => r.json());
    if (!data.length) return;

    const last = data[data.length - 1];
    document.getElementById('wr').textContent = (last.win_rate * 100).toFixed(1) + '%';
    document.getElementById('ep').textContent = last.episode;
    document.getElementById('eps').textContent = last.epsilon.toFixed(3);
    document.getElementById('total').textContent = data.length;

    chart.data.labels = data.map(d => d.episode);
    chart.data.datasets[0].data = data.map(d => d.win_rate);
    chart.update('none');

    const recent = data.slice(-10).reverse();
    document.getElementById('tbody').innerHTML = recent.map(d => `
      <tr>
        <td>${d.episode}</td>
        <td>${(d.win_rate * 100).toFixed(1)}%</td>
        <td>${d.epsilon.toFixed(3)}</td>
        <td><span class="badge ${d.win_rate >= 0.5 ? 'win' : 'loss'}">${d.win_rate >= 0.5 ? 'WIN' : 'LOSS'}</span></td>
      </tr>`).join('');

    document.getElementById('status').textContent =
      'Último update: ' + new Date().toLocaleTimeString();
  } catch(e) { /* servidor no listo */ }
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon RL Dashboard — http://localhost:9000  ║")
    print("╚══════════════════════════════════════════════════╝")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="warning")
