# Grafana Dashboard pour Lucide Pipeline

Ce dossier contient les dashboards Grafana pour monitorer le pipeline des agents Lucide.

## Installation

### 1. Installer Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64
```

### 2. Configurer Prometheus

Créer `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'lucide'
    static_configs:
      - targets: ['localhost:8000']  # Backend FastAPI
    metrics_path: '/metrics'
```

### 3. Lancer Prometheus

```bash
./prometheus --config.file=prometheus.yml
```

Prometheus sera disponible sur `http://localhost:9090`

### 4. Installer Grafana

```bash
# Ubuntu/Debian
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/enterprise/release/grafana-enterprise_10.0.0_amd64.deb
sudo dpkg -i grafana-enterprise_10.0.0_amd64.deb

# OU via Docker
docker run -d -p 3000:3000 --name=grafana grafana/grafana
```

### 5. Configurer Grafana

1. Accéder à Grafana: `http://localhost:3000`
2. Login: admin / admin (changer le mot de passe)
3. Ajouter Prometheus comme data source:
   - Configuration → Data Sources → Add data source
   - Sélectionner "Prometheus"
   - URL: `http://localhost:9090`
   - Save & Test

### 6. Importer les dashboards

1. Dashboards → Import
2. Upload `lucide_pipeline_dashboard.json`
3. Sélectionner Prometheus data source
4. Import

## Dashboards disponibles

### 1. Performance Dashboard

**Métriques principales:**
- **Pipeline Latency** (p50, p95, p99) par intent
- **Component Duration** (stacked bar chart)
  - Intent detection
  - Tool execution
  - Causal analysis
  - Data analysis
  - Response generation
- **Requests per minute** (time series)
- **Error rate** par étape (gauge)

**Panels:**
```
┌─────────────────────────────────────────────────────────┐
│ Pipeline Latency (p95)                                  │
│ [Time Series Graph]                                      │
│ - analyse_rencontre: 8.5s                              │
│ - stats_live: 3.2s                                      │
│ - classement_ligue: 1.8s                               │
└─────────────────────────────────────────────────────────┘

┌───────────────────────┬─────────────────────────────────┐
│ Component Duration    │ Requests per Minute             │
│ [Stacked Bar]         │ [Time Series]                   │
│                       │                                 │
│ Intent: 0.5s          │ 60 rpm ↗                       │
│ Tools: 3.0s           │                                 │
│ Analysis: 1.5s        │                                 │
│ Response: 1.0s        │                                 │
└───────────────────────┴─────────────────────────────────┘

┌───────────────────────┬─────────────────────────────────┐
│ Error Rate            │ Success Rate                    │
│ [Gauge]               │ [Gauge]                         │
│                       │                                 │
│     1.2%              │     98.8%                      │
│                       │                                 │
└───────────────────────┴─────────────────────────────────┘
```

### 2. API Dashboard

**Métriques:**
- **API calls per endpoint** (bar chart)
- **API call duration** (heatmap)
- **API failures** (pie chart par error_type)
- **Cache hit rate** (gauge + time series)
- **Parallel execution count** (counter)

**Panels:**
```
┌─────────────────────────────────────────────────────────┐
│ Top API Endpoints (calls/min)                           │
│ [Bar Chart]                                              │
│                                                          │
│ fixtures_search        ████████████████ 45              │
│ team_statistics        ████████████ 30                  │
│ standings              ████████ 20                      │
│ top_scorers            ████ 10                         │
└─────────────────────────────────────────────────────────┘

┌───────────────────────┬─────────────────────────────────┐
│ API Call Duration     │ Cache Hit Rate                  │
│ [Heatmap]             │ [Gauge + Time Series]           │
│                       │                                 │
│ fixtures_search: 0.5s │     75%                        │
│ team_stats: 1.2s      │ [Graph showing trend]          │
│ standings: 0.8s       │                                 │
└───────────────────────┴─────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ API Failures by Type                                    │
│ [Pie Chart]                                              │
│                                                          │
│ 🔴 Timeout: 45%                                         │
│ 🟠 Not Found: 30%                                       │
│ 🟡 Rate Limit: 15%                                      │
│ 🔵 Other: 10%                                           │
└─────────────────────────────────────────────────────────┘
```

### 3. Cost Dashboard

**Métriques:**
- **LLM calls** par modèle (time series)
- **LLM tokens used** (cumulative)
- **Estimated cost per request** (stat panel)
- **Template usage rate** (gauge - cost savings)
- **Cost savings** from optimizations

**Panels:**
```
┌─────────────────────────────────────────────────────────┐
│ LLM Usage by Model                                      │
│ [Stacked Area Chart]                                    │
│                                                          │
│ GPT-4o (Fast):     ████████ 40%                        │
│ GPT-4o-mini (Med): ████████████ 50%                    │
│ DeepSeek (Slow):   ██ 10%                              │
└─────────────────────────────────────────────────────────┘

┌───────────────────────┬─────────────────────────────────┐
│ Cost per Request      │ Template Usage Rate             │
│ [Stat]                │ [Gauge]                         │
│                       │                                 │
│   $0.018              │     35%                        │
│   (-28% vs baseline)  │ (saving $0.01/req)             │
└───────────────────────┴─────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Token Usage (millions)                                  │
│ [Time Series]                                            │
│                                                          │
│ Prompt tokens:     ████████████ 2.5M                   │
│ Completion tokens: ████████ 1.8M                        │
│ Total:             4.3M                                  │
└─────────────────────────────────────────────────────────┘
```

## Alertes recommandées

### 1. High Latency Alert

```yaml
alert: HighPipelineLatency
expr: histogram_quantile(0.95, pipeline_duration_seconds) > 10
for: 5m
labels:
  severity: warning
annotations:
  summary: "Pipeline latency too high"
  description: "P95 latency is {{ $value }}s (threshold: 10s)"
```

### 2. High Error Rate

```yaml
alert: HighErrorRate
expr: (rate(pipeline_failure_total[5m]) / rate(pipeline_requests_total[5m])) > 0.05
for: 5m
labels:
  severity: critical
annotations:
  summary: "Error rate above 5%"
  description: "Current error rate: {{ $value }}%"
```

### 3. Low Cache Hit Rate

```yaml
alert: LowCacheHitRate
expr: cache_hit_rate < 0.5
for: 10m
labels:
  severity: warning
annotations:
  summary: "Cache hit rate below 50%"
  description: "Current hit rate: {{ $value }}"
```

### 4. High API Failure Rate

```yaml
alert: HighAPIFailureRate
expr: (rate(api_call_failures_total[5m]) / rate(api_calls_executed_total[5m])) > 0.10
for: 5m
labels:
  severity: critical
annotations:
  summary: "API failure rate above 10%"
  description: "Failure rate: {{ $value }}%"
```

## Métriques disponibles

Voir `backend/monitoring/autonomous_agents_metrics.py` pour la liste complète.

**Principales métriques:**

| Métrique | Type | Description |
|----------|------|-------------|
| `pipeline_requests_total` | Counter | Nombre total de requêtes |
| `pipeline_duration_seconds` | Histogram | Durée totale du pipeline |
| `component_duration_seconds` | Histogram | Durée par composant |
| `api_calls_executed_total` | Counter | Nombre d'appels API |
| `api_call_duration_seconds` | Histogram | Durée des appels API |
| `cache_hit_rate` | Gauge | Taux de hit cache |
| `llm_calls_total` | Counter | Nombre d'appels LLM |
| `llm_tokens_used_total` | Counter | Tokens utilisés |

## Queries PromQL utiles

### Latence moyenne par intent

```promql
rate(pipeline_duration_seconds_sum[5m]) / rate(pipeline_duration_seconds_count[5m])
```

### Top 5 endpoints API

```promql
topk(5, sum(rate(api_calls_executed_total[5m])) by (endpoint_name))
```

### Coût LLM estimé (GPT-4o @ $0.03/1M tokens)

```promql
sum(rate(llm_tokens_used_total{model="gpt-4o"}[1h])) * 3600 * 0.03 / 1000000
```

### Économies des templates (appels LLM évités)

```promql
sum(rate(pipeline_requests_total{question_type=~"standings|top_scorers|top_assists"}[5m]))
```

## Troubleshooting

### Métriques ne s'affichent pas

1. Vérifier que Prometheus scrape bien le backend:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Vérifier les targets Prometheus:
   - Aller sur `http://localhost:9090/targets`
   - Vérifier que `lucide` est UP

3. Vérifier la connexion Grafana ↔ Prometheus:
   - Configuration → Data Sources → Prometheus
   - Cliquer "Test" en bas

### Dashboard vide

1. Vérifier qu'il y a du trafic:
   ```bash
   curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Classement Ligue 1"}'
   ```

2. Ajuster la time range dans Grafana (en haut à droite)

3. Vérifier les queries dans les panels (Edit → Query)

## Maintenance

### Exporter le dashboard

```bash
# API Grafana
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/dashboards/uid/lucide-pipeline \
  | jq '.dashboard' > lucide_pipeline_dashboard.json
```

### Mettre à jour les alertes

1. Alerting → Alert rules
2. Edit rule
3. Save

### Nettoyer les anciennes données Prometheus

```bash
# Retention par défaut: 15 jours
# Pour changer: --storage.tsdb.retention.time=30d
```

## Support

Pour toute question:
- Backend metrics: `backend/monitoring/autonomous_agents_metrics.py`
- Grafana docs: https://grafana.com/docs/
- Prometheus docs: https://prometheus.io/docs/
