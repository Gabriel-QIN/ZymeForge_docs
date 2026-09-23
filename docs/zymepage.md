# ZymePage Registry Catalog

ZymePage is the browser-facing catalog for ZymeForge. Registry metadata is available on this static page immediately; when a ZymeForge API URL is connected, the catalog refreshes from the live `/api/registries` endpoint and reaction mining can be run from the same page.

<div id="zymepage-catalog" class="zf-registry-app" data-default-api="">
  <div class="zf-catalog-head">
    <div>
      <span class="zf-kicker">ZymePage · Registry catalog V1</span>
      <h2>Enzyme discovery, organized by capability.</h2>
      <p>Browse the registered workflows and model adapters that connect reaction, sequence, structure, function, and engineering evidence.</p>
    </div>
    <div class="zf-connection">
      <label for="zf-api-url">ZymeForge API</label>
      <div class="zf-api-row">
        <input id="zf-api-url" type="url" placeholder="https://your-api.example.com" autocomplete="url">
        <button id="zf-connect" type="button">Connect</button>
      </div>
      <small id="zf-api-status" role="status">Showing the built-in registry snapshot</small>
    </div>
  </div>

  <div class="zf-catalog-layout">
    <aside class="zf-registry-nav" aria-label="Registry navigation">
      <span class="zf-nav-label">Registries</span>
      <nav id="zf-registry-links"></nav>
    </aside>
    <div id="zf-registry-sections" class="zf-registry-sections"></div>
  </div>

  <section class="zf-runner" aria-labelledby="zf-runner-title">
    <div>
      <span class="zf-kicker">Live workflow</span>
      <h2 id="zf-runner-title">Reaction-to-Enzyme Mining</h2>
      <p>Submit reaction SMILES to the connected ZymeForge API and inspect ranked candidates, evidence, and ZymeScore.</p>
    </div>
    <form id="zf-reaction-form">
      <label for="zf-reaction">Reaction SMILES</label>
      <div class="zf-api-row">
        <input id="zf-reaction" name="reaction" value="CCO.O&gt;&gt;CC=O.O" required>
        <button type="submit">Run mining</button>
      </div>
      <pre id="zf-reaction-output" aria-live="polite">Connect an API to run this workflow.</pre>
    </form>
  </section>

  <section class="zf-runner" aria-labelledby="zf-substrate-title">
    <div>
      <span class="zf-kicker">Live discovery</span>
      <h2 id="zf-substrate-title">Substrate-to-Enzyme Mining</h2>
      <p>Submit SMILES, InChI, InChIKey, or a substrate name to the connected ZymeForge API.</p>
    </div>
    <form id="zf-substrate-form">
      <label for="zf-substrate">Substrate query</label>
      <div class="zf-api-row">
        <input id="zf-substrate" name="query" value="CCO" required>
        <button type="submit">Find enzymes</button>
      </div>
      <pre id="zf-substrate-output" aria-live="polite">Connect an API to run this workflow.</pre>
    </form>
  </section>
</div>

The catalog is static by design so it can be hosted by GitHub Pages. The API URL is stored in this browser only; it can point to a local `zymepage web` process or a separately deployed FastAPI service.
