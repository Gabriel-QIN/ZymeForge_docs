# ZymePage

Documentation and the registry-backed model catalog for [ZymeForge](https://github.com/Gabriel-QIN/ZymeForge).

- Documentation: <https://gabriel-qin.github.io/ZymeForge_docs/>
- Registry catalog: <https://gabriel-qin.github.io/ZymeForge_docs/zymepage/>
- Core framework: <https://github.com/Gabriel-QIN/ZymeForge>

## Documentation

```bash
python -m pip install --index-url https://pypi.org/simple -e ".[docs]"
mkdocs serve
```

Build the deployable site:

```bash
mkdocs build --strict
```

## Model catalog

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Gabriel-QIN/ZymeForge_docs)

The catalog reads Functional Prediction Registry metadata directly from the installed ZymeForge package.

```bash
python -m pip install --index-url https://pypi.org/simple -e ".[web]"
zymepage web
```

The `web` extra installs the core ZymeForge package from its public GitHub repository over HTTPS.

Open <http://127.0.0.1:8000/tools>. The Harness interface is available at
`/harness`, with compile/run/status APIs under `/api/harness`. The registry API
is available at `/api/registries`, the model API at `/api/models`, reaction
mining at `/api/reactions/mine`, general reaction discovery at
`/api/reactions/discover`, substrate discovery at `/api/substrates/mine`, and
multi-representation protein retrieval at `/api/similarity/search`. OpenAPI
documentation is at `/api/docs`.

Registered adapters without configured upstream weights return an explicit HTTP `503`; the interface does not generate placeholder predictions.
