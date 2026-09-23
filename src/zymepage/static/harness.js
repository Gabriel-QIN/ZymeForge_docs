(() => {
  const query = document.querySelector("#harness-query");
  const compileButton = document.querySelector("#harness-compile");
  const runButton = document.querySelector("#harness-run");
  const message = document.querySelector("#harness-message");
  const parsed = document.querySelector("#parsed-task");
  const plan = document.querySelector("#harness-plan");
  const funnel = document.querySelector("#candidate-funnel");
  const runState = document.querySelector("#run-state");
  const results = document.querySelector("#harness-results");
  if (!query || !compileButton) return;
  let agentRequest = null;

  const call = async (url, body) => {
    const response = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
    return payload;
  };

  const renderPlan = (request, state = null) => {
    plan.innerHTML = "";
    request.steps.forEach((step) => {
      const item = document.createElement("li");
      const completed = state?.completed_steps?.includes(step.step_id);
      const running = state?.current_step === step.step_id;
      item.className = completed ? "complete" : running ? "running" : "pending";
      item.innerHTML = `<span>${completed ? "✓" : running ? "→" : "○"}</span><div><strong>${step.capability}</strong><small>${step.step_id} · depends on ${step.depends_on.join(", ") || "none"}</small></div>`;
      plan.appendChild(item);
    });
  };

  compileButton.addEventListener("click", async () => {
    if (!query.value.trim()) return;
    compileButton.disabled = true;
    runButton.disabled = true;
    message.textContent = "Compiling a constrained AgentRequest…";
    try {
      agentRequest = await call("/api/harness/compile", {query: query.value});
      parsed.innerHTML = `<dl><dt>Task</dt><dd>${agentRequest.task_type}</dd><dt>Target</dt><dd><code>${JSON.stringify(agentRequest.target)}</code></dd><dt>Constraints</dt><dd><code>${JSON.stringify(agentRequest.constraints)}</code></dd></dl>`;
      renderPlan(agentRequest);
      results.textContent = JSON.stringify(agentRequest, null, 2);
      message.textContent = agentRequest.missing_information.length ? `Missing: ${agentRequest.missing_information.join(", ")}` : "Plan compiled and locally schema-valid.";
      runButton.disabled = false;
    } catch (error) {
      message.textContent = error.message;
    } finally {
      compileButton.disabled = false;
    }
  });

  runButton.addEventListener("click", async () => {
    runButton.disabled = true;
    message.textContent = "Submitting validated workflow…";
    try {
      const created = await call("/api/harness/run", {query: query.value, agent_request: agentRequest});
      let state;
      for (let attempt = 0; attempt < 360; attempt += 1) {
        const response = await fetch(`/api/harness/runs/${created.run_id}`);
        if (response.ok) {
          state = await response.json();
          renderPlan(agentRequest, state);
          funnel.textContent = state.candidate_count.toLocaleString();
          runState.textContent = state.status;
          results.textContent = JSON.stringify(state, null, 2);
          if (["COMPLETED", "FAILED", "WAITING_FOR_INPUT"].includes(state.status)) break;
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      message.textContent = state ? `Run ${state.run_id}: ${state.status}` : "Run status unavailable.";
    } catch (error) {
      message.textContent = error.message;
    } finally {
      runButton.disabled = false;
    }
  });
})();
