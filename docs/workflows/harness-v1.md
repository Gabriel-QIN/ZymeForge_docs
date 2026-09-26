# Harness V2

Harness V2 turns a natural-language scientific request into a reproducible,
environment-aware
ZymeForge workflow without giving an LLM shell or server access.

```text
Natural language
    ↓
live PlanningContext
    ↓
LLM Structured Output
    ↓
AgentRequest + PlanStep DAG
    ↓
local validation
    ↓
deterministic capability routing
    ↓
registered ZymeForge tools
    ↓
Candidate records + provenance
```

## PlanningContext

Before compilation, ZymeForge snapshots the state of the current installation.
The planner receives registered model/tool IDs and versions, input requirements,
output contracts, allowlisted parameter ranges, relative cost, CPU/GPU needs,
database metadata, and live binary/checkpoint/database/license/handler health.

```bash
zymeforge harness context --output planning_context.json
```

Every `PlanStep` may contain validated `preferred_tools`. A provider must be
registered for that capability, and all parameters remain allowlisted. When no
provider is requested explicitly, the deterministic router prefers healthy
routes. Inputs required to start, optional clarifications, and missing server
assets are recorded separately. Unavailable providers are omitted from the
executable DAG so preliminary retrieval can still run without fabricated scores.

Function-first requests are supported through the reviewed UniProt REST search.
For example, “I need a high-activity reverse transcriptase at pH 6–8” can begin
with name/EC sequence retrieval and preliminary ranking. EpHod/OphPred and
CataPro/UniKP/TurNuP remain explicit missing evidence until their official model
assets and handlers are configured.

## What the LLM can do

The compiler may identify the task, target, constraints, objectives, output
requirements, missing inputs, and the required capabilities. It emits a strict
Pydantic Structured Output object.

It cannot choose executables, invent tool names, provide arbitrary model flags,
run shell commands, install dependencies, or change a plan during execution.
It can select registered provider IDs; defaults, parameter allowlists, fixed
fallbacks, and availability checks remain controlled by the server-owned Tool
Registry.

## Supported task families

- enzyme discovery;
- substrate- and reaction-based discovery;
- remote homology and structure search;
- function prediction;
- mutation prediction;
- sequence redesign.

The included 50-task benchmark contains realistic reverse-transcriptase sequence
mining and PET/BHET reaction-mining cases. It measures schema, task, target,
constraint, capability and provider accuracy, PlanningContext usage,
missing-input detection, environment awareness, readiness and plan validity.

## Execution states

Runs use `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, and
`WAITING_FOR_INPUT`. If required scientific input is absent, the request enters
`WAITING_FOR_INPUT` before any expensive provider starts. Harness V2 stops after
a failed step and never asks an LLM to replan.

Each run produces `run.json`, `agent_request.json`, `planning_context.json`,
`resolved_plan.json`, per-tool results, `candidates.csv`, `provenance.json`, and
`report.html`.

## CLI

```bash
export OPENAI_API_KEY=...
zymeforge harness plan "Find remote PETases below 30% identity"
zymeforge harness run "Find remote PETases below 30% identity"
zymeforge harness benchmark --validate-only
zymeforge harness benchmark
```

An OpenAI-compatible relay may be used by setting its base URL and an exact
model name exposed by that service:

```bash
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://relay.example/v1
export ZYMEFORGE_LLM_MODEL=relay-model-name
```

Harness tries Responses Structured Outputs first. For relays that reject open
scientific metadata objects in a strict JSON Schema, it falls back to Chat
Completions JSON Object mode. Every result is still checked by Pydantic and the
local Registry/DAG validator, with at most one repair attempt. Invalid provider
names, parameters, inputs or dependencies are not executed.

The preflight validates all 50 definitions and current environment readiness
without an LLM. The live benchmark requires `OPENAI_API_KEY`; missing credentials
produce an explicit error, never placeholder scores.

An existing request can be executed without another model call:

```bash
zymeforge harness run "PETase discovery" --request-file agent_request.json
```

## API

Compile a request:

```http
POST /api/harness/compile
Content-Type: application/json

{"query": "Find remote PETases below 30% identity"}
```

Start a validated request:

```http
POST /api/harness/run
Content-Type: application/json

{"query": "...", "agent_request": { ... }}
```

Read run state:

```http
GET /api/harness/runs/{run_id}
```

ZymePage exposes an interactive Harness view at `/harness`. External indexes,
checkpoints, databases, and source directories are configured only on the
server. Client-supplied server filesystem paths are rejected.

## V2 boundary

Harness V2 does not implement reflection, critic loops, multi-agent execution,
autonomous installation, persistent scientific memory, or observe-and-replan.
Those behaviors are intentionally outside this release.
