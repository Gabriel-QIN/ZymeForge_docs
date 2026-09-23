# Harness V1

Harness V1 turns a natural-language scientific request into a reproducible
ZymeForge workflow without giving an LLM shell or server access.

```text
Natural language
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

## What the LLM can do

The compiler may identify the task, target, constraints, objectives, output
requirements, missing inputs, and the required capabilities. It emits a strict
Pydantic Structured Output object.

It cannot choose executables, invent tool names, provide arbitrary model flags,
run shell commands, install dependencies, or change a plan during execution.
Provider selection, defaults, parameter allowlists, fixed fallbacks, and
availability checks come from the server-owned Tool Registry.

## Supported task families

- enzyme discovery;
- substrate- and reaction-based discovery;
- remote homology and structure search;
- function prediction;
- mutation prediction;
- sequence redesign.

The included 50-task benchmark measures schema validity, task classification,
constraint extraction, capability selection, missing-input detection, and plan
validity.

## Execution states

Runs use `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, and
`WAITING_FOR_INPUT`. If required scientific input is absent, the request enters
`WAITING_FOR_INPUT` before any expensive provider starts. Harness V1 stops after
a failed step and never asks an LLM to replan.

Each run produces `run.json`, `agent_request.json`, `resolved_plan.json`,
per-tool results, `candidates.csv`, `provenance.json`, and `report.html`.

## CLI

```bash
export OPENAI_API_KEY=...
zymeforge harness plan "Find remote PETases below 30% identity"
zymeforge harness run "Find remote PETases below 30% identity"
zymeforge harness benchmark
```

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

## V1 boundary

Harness V1 does not implement reflection, critic loops, multi-agent execution,
autonomous installation, persistent scientific memory, or observe-and-replan.
Those behaviors are intentionally outside this release.
