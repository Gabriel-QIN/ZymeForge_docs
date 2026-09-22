# Web catalog

ZymePage provides searchable model cards and input forms backed by the same Python registry used by the ZymeForge CLI.

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

## API

The web process also exposes:

| Endpoint | Purpose |
|---|---|
| `GET /api/models` | all registered model cards |
| `GET /api/models/{id}` | one model/task adapter |
| `POST /api/models/{id}/predict` | validated inference request |
| `GET /api/docs` | interactive OpenAPI reference |

An adapter without an installed runner and weights returns HTTP `503` with a configuration message. This keeps registration, deployment status, and inference results distinct.
