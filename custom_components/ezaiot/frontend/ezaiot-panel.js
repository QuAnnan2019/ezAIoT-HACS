class EzaiotPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._loadStatus();
  }

  connectedCallback() {
    this.attachShadow({ mode: "open" });
    this._render();
  }

  async _loadStatus(force = false) {
    if (!this._hass || this._loading) return;
    if (!force && Date.now() - (this._lastRefresh || 0) < 30000) return;

    this._loading = true;
    this._lastRefresh = Date.now();
    this._render();
    try {
      this._status = await this._hass.callWS({ type: "ezaiot/status" });
      this._error = null;
    } catch (error) {
      this._error = "Unable to load local ezAIoT status.";
    } finally {
      this._loading = false;
      this._render();
    }
  }

  _render() {
    if (!this.shadowRoot) return;

    const status = this._status;
    const deviceContent = !status
      ? "<p class=\"muted\">Loading local compatibility status...</p>"
      : status.records.length === 0
        ? "<p class=\"muted\">No matching Rti-Tek eTRV-ZB01 devices were found in ZHA.</p>"
        : status.records.map((record) => `
          <li>
            <strong>${record.manufacturer} ${record.model}</strong>
            <span>Supported device ${record.ordinal} · ${record.entity_count} entities</span>
          </li>
        `).join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; background: var(--primary-background-color); color: var(--primary-text-color); min-height: 100%; }
        main { max-width: 1120px; margin: 0 auto; padding: 32px 24px 56px; }
        header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin-bottom: 28px; }
        h1 { font-size: 30px; font-weight: 500; margin: 0 0 8px; }
        h2 { font-size: 18px; margin: 0 0 16px; }
        p { margin: 0; line-height: 1.55; }
        .subtitle, .muted, li span { color: var(--secondary-text-color); }
        .refresh { border: 0; background: var(--secondary-background-color); color: var(--primary-text-color); border-radius: 50%; height: 40px; width: 40px; font-size: 21px; cursor: pointer; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
        section { border: 1px solid var(--divider-color); border-radius: 8px; padding: 22px; background: var(--card-background-color, var(--primary-background-color)); }
        .metric { font-size: 48px; font-weight: 500; line-height: 1; margin-bottom: 10px; }
        .state { color: var(--success-color, #1b873f); }
        .warning { color: var(--warning-color, #b26a00); }
        ul { list-style: none; margin: 0; padding: 0; }
        li { border-top: 1px solid var(--divider-color); display: flex; flex-direction: column; gap: 5px; padding: 14px 0; }
        li:first-child { border-top: 0; padding-top: 0; }
        .wide { grid-column: 1 / -1; }
        a { color: var(--primary-color); text-decoration: none; }
        .error { color: var(--error-color); margin-top: 12px; }
      </style>
      <main>
        <header>
          <div>
            <h1>ezAIoT</h1>
            <p class="subtitle">Local device compatibility, guidance, and support.</p>
          </div>
          <button class="refresh" title="Refresh" aria-label="Refresh local status">↻</button>
        </header>
        <div class="grid">
          <section>
            <h2>Supported devices</h2>
            <div class="metric">${status ? status.supported_count : "—"}</div>
            <p class="${status && status.supported_count > 0 ? "state" : "muted"}">${status && status.supported_count > 0 ? "Exact-match ZHA devices found" : "Rti-Tek eTRV-ZB01 exact matches only"}</p>
          </section>
          <section>
            <h2>Quirk updates</h2>
            <p class="warning">${status ? status.update_source.message : "Loading update source status..."}</p>
            <p class="muted" style="margin-top:12px">No GitHub request is made until a trusted release source is configured.</p>
          </section>
          <section class="wide">
            <h2>Compatibility</h2>
            <ul>${deviceContent}</ul>
          </section>
          <section class="wide">
            <h2>Diagnostics and help</h2>
            <p>Use <a href="/config/integrations" target="_self">Settings → Devices & services</a> to open ezAIoT and download its native, redacted diagnostics before requesting support.</p>
          </section>
        </div>
        ${this._error ? `<p class="error">${this._error}</p>` : ""}
      </main>
    `;
    this.shadowRoot.querySelector(".refresh")?.addEventListener("click", () => this._loadStatus(true));
  }
}

customElements.define("ezaiot-panel", EzaiotPanel);
