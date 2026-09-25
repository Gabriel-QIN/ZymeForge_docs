# Installation

ZymeForge uses one shared Conda environment for the framework, model adapters, web catalog, and documentation.

## Requirements

- Linux x86-64
- Conda or Miniforge
- Python 3.11
- NVIDIA driver compatible with CUDA 12.8
- CUDA-capable NVIDIA GPU

## Create the environment

```bash
git clone https://github.com/Gabriel-QIN/ZymeForge.git
cd ZymeForge
make install
conda activate zymeforge
```

The installer uses the official conda-forge and PyPI endpoints. PyTorch is installed from the official CUDA 12.8 wheel index as `torch==2.11.0+cu128`.

Verify the installation:

```bash
python -c 'import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())'
zymeforge --help
zymeforge models
```

Expected CUDA fields are `2.11.0+cu128`, `12.8`, and `True`.

## Local database configuration

The general configuration maps stable database names to paths under
`/mnt/data2/database`. Inspect the current machine with:

```bash
zymeforge database list
zymeforge database resolve uniref90 --kind sequence
```

The local deployment links these sequence collections without duplicating their source
files: AFESM, EEMC, GOPC, Logan, NR, and UniRef90. A one-million-sequence UniRef90 example
and its persistent MMseqs2 index are also configured.

Database entries live under `databases` in `configs/default.yaml`. Set
`ZYMEFORGE_CONFIG` or pass `--database-config` to use another general configuration.
Commands accept either a configured name or an explicit filesystem path.

AFDB is currently linked as a `foldseek_archive`. It is visible in the catalog but is not
reported as directly searchable until the 458G archive has been extracted into a valid
Foldseek database.

## Containers

```bash
docker compose build
docker compose run --rm zymeforge plugins
```

GPU-backed container execution requires the NVIDIA Container Toolkit on the host.

## Documentation deployment

The `ZymeForge_docs` workflow publishes this site with GitHub Pages. Before its first run, a repository administrator must open **Settings → Pages → Build and deployment** in the documentation repository and set **Source** to **GitHub Actions**. This is a one-time GitHub repository setting; the built-in workflow token cannot enable Pages itself.
