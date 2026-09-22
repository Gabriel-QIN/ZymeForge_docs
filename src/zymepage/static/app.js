// ZymePage catalog interactions
(() => {
  const search = document.querySelector("#tool-search");
  const category = document.querySelector("#category-filter");
  const cards = [...document.querySelectorAll(".tool-card")];
  const count = document.querySelector("#tool-count");
  const empty = document.querySelector("#empty-state");

  const filterTools = () => {
    if (!search || !category) return;
    const query = search.value.trim().toLowerCase();
    const selected = category.value;
    let visible = 0;
    cards.forEach((card) => {
      const matchesText = card.dataset.search.toLowerCase().includes(query);
      const matchesCategory = selected === "all" || card.dataset.category === selected;
      const show = matchesText && matchesCategory;
      card.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = `${visible} model${visible === 1 ? "" : "s"}`;
    empty.hidden = visible !== 0;
  };

  search?.addEventListener("input", filterTools);
  category?.addEventListener("change", filterTools);
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && search && document.activeElement !== search) {
      event.preventDefault();
      search.focus();
    }
  });

  const form = document.querySelector("#runner-form");
  const shell = document.querySelector(".tool-shell[data-tool-id]");
  const outputState = document.querySelector("#output-state");
  const placeholder = document.querySelector("#output-placeholder");
  const outputCode = document.querySelector("#output-code");
  const fillExample = document.querySelector("#fill-example");

  fillExample?.addEventListener("click", () => {
    form.querySelectorAll("[data-example]").forEach((input) => {
      input.value = input.dataset.example;
    });
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[type='submit']");
    const payload = Object.fromEntries(new FormData(form).entries());
    button.disabled = true;
    outputState.textContent = "Running";
    outputState.classList.remove("error");
    try {
      const response = await fetch(shell.dataset.endpoint || `/api/models/${shell.dataset.toolId}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      placeholder.hidden = true;
      outputCode.hidden = false;
      outputCode.textContent = JSON.stringify(result, null, 2);
      outputState.textContent = response.ok ? "Complete" : `HTTP ${response.status}`;
      outputState.classList.toggle("error", !response.ok);
    } catch (error) {
      placeholder.hidden = true;
      outputCode.hidden = false;
      outputCode.textContent = JSON.stringify({ detail: error.message }, null, 2);
      outputState.textContent = "Error";
      outputState.classList.add("error");
    } finally {
      button.disabled = false;
    }
  });
})();
