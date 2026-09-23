# Web catalog

ZymePage provides a static Registry Catalog for GitHub Pages and a live model catalog backed by the same Python registry used by the ZymeForge CLI.

The [ZymePage Registry Catalog](../zymepage.md) works without a server using the checked-in registry snapshot. Enter a deployed API URL on that page to refresh registry metadata and call reaction mining from the browser.

```bash
git clone https://github.com/Gabriel-QIN/ZymeForge_docs.git
cd ZymeForge_docs
python -m pip install --index-url https://pypi.org/simple -e ".[web]"
zymepage web
```

Open [http://127.0.0.1:8000/tools](http://127.0.0.1:8000/tools). To expose another interface or port:

```bash
zymepage web --host 0.0.0.0 --port 8080
```

## Public backend deployment

GitHub Pages serves the documentation only. Deploy the FastAPI service separately with Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Gabriel-QIN/ZymeForge_docs)

1. Open [Render](https://render.com) and choose **New → Blueprint**.
2. Connect `Gabriel-QIN/ZymeForge_docs` and select `render.yaml`.
3. Deploy the `zymepage-api` service.

Render will provide a URL such as `https://zymepage-api.onrender.com`. Its API endpoints are `/api/models`, `/api/docs`, and `/tools`.

The catalog is fully public after deployment. Registered adapters without their upstream model runner and weights return HTTP `503` rather than fabricated predictions.

## API

The web process also exposes:

| Endpoint | Purpose |
|---|---|
| `GET /api/models` | all registered model cards |
| `GET /api/tools` | model cards plus workflow tools |
| `GET /api/registries` | Proto-style registry groups and tool membership |
| `GET /api/models/{id}` | one model/task adapter |
| `POST /api/models/{id}/predict` | validated inference request |
| `POST /api/reactions/mine` | run ZymeForge reaction-to-enzyme mining |
| `POST /api/reactions/discover` | discover enzymes from reaction SMILES, EC, name, or description |
| `POST /api/substrates/mine` | discover enzymes from SMILES, InChI, InChIKey, or substrate name |
| `GET /api/docs` | interactive OpenAPI reference |

An adapter without an installed runner and weights returns HTTP `503` with a configuration message. This keeps registration, deployment status, and inference results distinct.
