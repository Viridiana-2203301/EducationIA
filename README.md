# CSV Analytics Platform 🔬

Plataforma web para análisis automático de múltiples datasets CSV con machine learning.

## ✨ Características

| Característica | Descripción |
|---|---|
| **📤 Carga múltiple** | Hasta 36 archivos CSV simultáneamente |
| **🔍 Profiling automático** | Detección de tipos, nulos, duplicados, estadísticas |
| **🧹 Limpieza inteligente** | Imputación, normalización, corrección de tipos |
| **🔗 Detección de relaciones** | Matching por nombres, semántica y valores |
| **🕸️ Grafo de relaciones** | Visualización D3.js interactiva |
| **🔄 Fusión automática** | Inner join, left join, multi-table joins |
| **📊 Correlaciones** | Pearson y Spearman con heatmaps |
| **🎯 Clustering** | K-Means y DBSCAN con auto-parámetros |
| **📉 PCA** | Reducción dimensional con scatter 2D |
| **⚠️ Anomalías** | Isolation Forest y Local Outlier Factor |
| **📈 Tendencias** | Detección de patrones temporales |
| **💡 Insights** | Explicaciones en lenguaje natural |

## 🏗️ Arquitectura

```
backend/               # FastAPI + Python
├── app/
│   ├── api/           # REST endpoints
│   ├── services/      # Profiler, cleaner, matcher, fusion
│   ├── analysis/      # ML: correlación, clustering, PCA, anomalías, tendencias
│   ├── pipelines/     # Orquestador del pipeline
│   ├── schemas/       # Modelos Pydantic
│   └── utils/         # Validadores
├── data/              # raw/, processed/, temp/
├── requirements.txt
└── main.py

frontend/              # Next.js + React
├── src/
│   ├── components/    # FileUpload, Charts, Graph, Insights
│   ├── pages/         # index, datasets, analysis
│   ├── services/      # API client (Axios)
│   ├── hooks/         # useAnalysis
│   └── styles/        # Design system (dark glassmorphism)
├── package.json
└── next.config.js
```

## 🚀 Inicio Rápido

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

El servidor inicia en `http://localhost:8000` (docs en `/docs`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La aplicación inicia en `http://localhost:3000`.

## 🔧 Stack Tecnológico

- **Backend**: FastAPI, Pandas, Polars, Scikit-learn, NetworkX, DuckDB
- **Frontend**: Next.js 14, React, Plotly.js, D3.js
- **ML**: K-Means, DBSCAN, PCA, Isolation Forest, LOF, Pearson/Spearman

## 📋 Pipeline de Análisis

1. **Carga** → Validación, detección de encoding
2. **Profiling** → Estadísticas por columna y dataset
3. **Limpieza** → Duplicados, nulos, normalización
4. **Relaciones** → Matching entre datasets
5. **Grafo** → Red de conexiones
6. **Fusión** → Joins automáticos
7. **ML** → Correlaciones, clusters, PCA, anomalías, tendencias
8. **Insights** → Generación automática en lenguaje natural

## 📡 API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/upload` | Subir archivos CSV |
| `GET` | `/api/datasets` | Listar datasets |
| `GET` | `/api/datasets/{id}/preview` | Preview de datos |
| `POST` | `/api/analysis/run` | Ejecutar análisis |
| `GET` | `/api/analysis/latest` | Último resultado |
| `GET` | `/api/relationships/graph` | Grafo de relaciones |
| `GET` | `/api/insights` | Insights generados |
