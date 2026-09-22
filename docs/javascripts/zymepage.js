(() => {
  const init = () => {
    const root = document.querySelector("#zymepage-catalog");
    if (!root || root.dataset.initialized === "true") return;
    root.dataset.initialized = "true";

  const snapshot = [
    { id: "reaction-mining", label: "Reaction Mining", intro: "Start from substrates, products, reaction SMILES, EC numbers, or names and retrieve enzyme candidates.", tools: [{ id: "reaction-to-enzyme--mining", name: "Reaction-to-Enzyme Mining", version: "workflow-1.0", category: "Reaction mining", introduction: "Search exact and similar reactions, infer EC classes, and rank enzyme candidates.", inputs: ["reaction"], outputs: ["ranked_candidates", "evidence", "zyme_score"], endpoint: "/api/reactions/mine", kind: "workflow" }] },
    { id: "sequence-search", label: "Sequence Search", intro: "Search sequence space with alignment, profile, and protein language model evidence.", tools: [] },
    { id: "structure-search", label: "Structure Search", intro: "Compare global folds and local catalytic geometry to recover remote enzyme relationships.", tools: [{ name: "GraphEC-AS", version: "adapter-1.0", category: "Catalytic site", introduction: "Identify residues and local geometry that support catalysis.", inputs: ["protein_sequence", "protein_structure"], outputs: ["catalytic_residues", "local_confidence"] }, { name: "EC-LMGraph", version: "adapter-1.0", category: "Catalytic site", introduction: "Identify residues and local geometry that support catalysis.", inputs: ["protein_sequence", "protein_structure"], outputs: ["catalytic_residues", "local_confidence"] }] },
    { id: "function-prediction", label: "Function Prediction", intro: "Profile EC function, substrate compatibility, kinetics, stability, and developability.", tools: [
      ["CLEAN", "EC & function", ["protein_sequence"], ["ec_number", "score"]], ["HIT-EC", "EC & function", ["protein_sequence"], ["ec_number", "score"]], ["EC-LMGraph", "EC & function", ["protein_sequence"], ["ec_number", "score"]],
      ["EZSpecificity", "Substrate specificity", ["protein_sequence", "substrate_smiles"], ["compatibility_probability"]], ["ProSmith", "Substrate specificity", ["protein_sequence", "substrate_smiles"], ["compatibility_probability"]], ["ESP", "Substrate specificity", ["protein_sequence", "substrate_smiles"], ["compatibility_probability"]],
      ["CataPro", "Kinetics", ["protein_sequence", "substrate_smiles"], ["kcat", "km", "kcat_per_km"]], ["UniKP", "Kinetics", ["protein_sequence", "substrate_smiles"], ["kcat", "km", "kcat_per_km"]], ["TurNuP", "Kinetics", ["protein_sequence", "substrate_smiles"], ["kcat"]],
      ["EpHod", "Optimal pH", ["protein_sequence"], ["optimum_ph"]], ["OphPred", "Optimal pH", ["protein_sequence"], ["optimum_ph"]], ["TemBERTure", "Thermostability", ["protein_sequence"], ["melting_temperature", "thermostability_class"]], ["TemStaPro", "Thermostability", ["protein_sequence"], ["thermostable_probability"]], ["DeepSTABp", "Thermostability", ["protein_sequence"], ["melting_temperature"]],
      ["NetSolP", "Solubility", ["protein_sequence"], ["solubility_probability"]], ["DISCODE", "Cofactor specificity", ["protein_sequence"], ["cofactor", "preference_probability"]], ["INSIGHT", "Cofactor specificity", ["protein_sequence"], ["cofactor", "preference_probability"]], ["SignalP", "Developability", ["protein_sequence"], ["signal_peptide", "cleavage_site", "probability"]], ["DeepTMHMM", "Developability", ["protein_sequence"], ["topology", "transmembrane_regions"]], ["DeepLoc", "Developability", ["protein_sequence"], ["localization", "probability"]]
    ].map((item) => Array.isArray(item) ? { name: item[0], version: "adapter-1.0", category: item[1], introduction: "Registered ZymeForge functional prediction adapter.", inputs: item[2], outputs: item[3] } : item) },
    { id: "structure-prediction", label: "Structure Prediction", intro: "Generate protein and complex structures for pocket inspection, docking, and consistency checks.", tools: [] },
    { id: "engineering", label: "Engineering", intro: "Move from a selected enzyme to targeted mutation optimization or sequence redesign.", tools: [{ name: "GeoStab", version: "adapter-1.0", category: "Mutation effects", introduction: "Estimate stability and fitness effects of a proposed mutation.", inputs: ["protein_structure", "mutation"], outputs: ["ddg", "ddtm", "fitness"] }, { name: "ThermoMPNN", version: "adapter-1.0", category: "Mutation effects", introduction: "Estimate stability and fitness effects of a proposed mutation.", inputs: ["protein_structure", "mutation"], outputs: ["ddg", "stability_probability"] }] },
    { id: "evidence-fusion", label: "Evidence Fusion", intro: "Calibrate heterogeneous evidence into an explainable ZymeScore and candidate ranking.", tools: [] },
    { id: "output", label: "Output", intro: "Export candidates, evidence, score cards, and provenance for downstream analysis.", tools: [] }
  ];

  const apiInput = root.querySelector("#zf-api-url");
  const connect = root.querySelector("#zf-connect");
  const status = root.querySelector("#zf-api-status");
  const nav = root.querySelector("#zf-registry-links");
  const sections = root.querySelector("#zf-registry-sections");
  const queryApi = new URLSearchParams(window.location.search).get("api") || "";
  let storedApi = queryApi || root.dataset.defaultApi || "";
  try { storedApi = storedApi || window.localStorage.getItem("zymeforge-api-url") || ""; } catch (_) { /* storage can be disabled */ }
  apiInput.value = storedApi;

  const esc = (value) => String(value ?? "").replace(/[&<>\"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '\"': "&quot;" }[char]));
  const apiBase = () => apiInput.value.trim().replace(/\/$/, "");
  const normalizeTools = (group) => group.tools || [];

  function render(groups) {
    nav.innerHTML = groups.map((group, index) => `<a href="#${esc(group.id)}"><span>${esc(group.label)}</span><em>${normalizeTools(group).length}</em></a>`).join("");
    sections.innerHTML = groups.map((group, index) => {
      const tools = normalizeTools(group);
      const cards = tools.length ? tools.map((tool) => `<article class="zf-tool-card"><div class="zf-tool-top"><span class="zf-tool-tag">${esc(tool.category || tool.task || "Registry tool")}</span><span>${esc(tool.kind || "model")}</span></div><h4>${esc(tool.name)}</h4><p>${esc(tool.introduction || tool.description || "Registered ZymeForge adapter.")}</p><div class="zf-tool-meta"><span>v${esc(tool.version || "unspecified")}</span><span>${esc((tool.inputs || []).join(" + "))} -> ${esc((tool.outputs || []).join(" / "))}</span></div>${tool.endpoint && apiBase() ? `<p><a href="${esc(apiBase() + tool.endpoint)}" target="_blank" rel="noreferrer">Open API endpoint</a></p>` : ""}</article>`).join("") : `<div class="zf-empty">No adapters are registered in this registry yet. The capability boundary is ready for a plugin.</div>`;
      return `<section class="zf-registry-section" id="${esc(group.id)}"><div class="zf-registry-section-head"><h3>${String(index + 1).padStart(2, "0")} - ${esc(group.label)}</h3><span>${tools.length} registered</span></div><p class="zf-registry-intro">${esc(group.intro || "Registered ZymeForge capability boundary.")}</p><div class="zf-tool-grid">${cards}</div></section>`;
    }).join("");
  }

  async function refresh() {
    render(snapshot);
    const base = apiBase();
    if (!base) {
      status.textContent = "Showing the built-in registry snapshot";
      return;
    }
    status.textContent = "Connecting...";
    try {
      const response = await fetch(`${base}/api/registries`, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      render(payload.registries || snapshot);
      try { window.localStorage.setItem("zymeforge-api-url", base); } catch (_) { /* storage can be disabled */ }
      status.textContent = `Connected - ${payload.count || 0} registries`;
    } catch (error) {
      status.textContent = `API unavailable - showing snapshot (${error.message})`;
    }
  }

  connect.addEventListener("click", refresh);
  render(snapshot);

  const form = root.querySelector("#zf-reaction-form");
  const output = root.querySelector("#zf-reaction-output");
    form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const base = apiBase();
    if (!base) { output.textContent = "Enter a deployed ZymeForge API URL first."; return; }
    output.textContent = "Running...";
    try {
      const response = await fetch(`${base}/api/reactions/mine`, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ reaction: root.querySelector("#zf-reaction").value, top_k: 20 }) });
      const payload = await response.json();
      output.textContent = JSON.stringify(payload, null, 2);
    } catch (error) { output.textContent = JSON.stringify({ detail: error.message }, null, 2); }
    });
  };

  if (typeof document$ !== "undefined") document$.subscribe(init);
  else init();
})();
