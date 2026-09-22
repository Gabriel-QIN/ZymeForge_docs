# ZymePage

Documentation and the registry-backed model catalog for [ZymeForge](https://github.com/Gabriel-QIN/ZymeForge).

- Documentation: <https://gabriel-qin.github.io/ZymeForge_docs/>
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

The catalog reads Functional Prediction Registry metadata directly from the installed ZymeForge package.

```bash
python -m pip install --index-url https://pypi.org/simple -e ".[web]"
zymepage web
```

The `web` extra installs the core ZymeForge package from its GitHub repository over SSH, so GitHub authentication must be configured for private-repository access.

Open <http://127.0.0.1:8000/tools>. The model API is available at `/api/models`, with OpenAPI documentation at `/api/docs`.

Registered adapters without configured upstream weights return an explicit HTTP `503`; the interface does not generate placeholder predictions.
