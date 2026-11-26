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

  _escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async _runReleaseAction(type, confirmation) {
    if (!this._hass || this._releaseAction) return;
    if (confirmation && !window.confirm(confirmation)) return;

    this._releaseAction = type;
    this._render();
    try {
      await this._hass.callWS({ type });
      await this._loadStatus(true);
    } catch (error) {
      this._error = "Unable to complete the test Release action.";
    } finally {
      this._releaseAction = null;
      this._render();
    }
  }

  async _downloadDiagnostics() {
    if (!this._hass || this._diagnosticsAction) return;

    this._diagnosticsAction = true;
    this._render();
    try {
      const diagnostics = await this._hass.callWS({
        type: "ezaiot/download_diagnostics",
      });
      const blob = new Blob([JSON.stringify(diagnostics, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "ezaiot-diagnostics.json";
      link.click();
      URL.revokeObjectURL(url);
      this._error = null;
    } catch (error) {
      this._error = "Unable to download local ezAIoT diagnostics.";
    } finally {
      this._diagnosticsAction = false;
      this._render();
    }
  }

  async _dismissCompletion() {
    if (!this._hass) return;
    await this._hass.callWS({ type: "ezaiot/dismiss_completion" });
    await this._loadStatus(true);
  }

  _render() {
    if (!this.shadowRoot) return;

    const status = this._status;
    const release = status?.update_source;
    const guidance = status?.guidance;
    const support = status?.support;
    const onboarding = status?.onboarding;
    const isAdmin = this._hass?.user?.is_admin === true;
    const actionInProgress = Boolean(this._releaseAction);
    const hasBackup = Boolean(release?.backup_version);
    const canInstall = release?.state === "update_available";
    const releaseNotes = this._escape(release?.release_notes);
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
        .test-mode { color: var(--error-color); font-weight: 600; margin-bottom: 8px; }
        .release-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
        .release-actions button { border: 1px solid var(--primary-color); border-radius: 4px; background: transparent; color: var(--primary-color); min-height: 36px; padding: 0 14px; cursor: pointer; }
        .release-actions button.primary { background: var(--primary-color); color: var(--text-primary-color, white); }
        .release-actions button:disabled { cursor: default; opacity: 0.5; }
        .guidance pre { background: var(--secondary-background-color); border: 1px solid var(--divider-color); margin: 14px 0; overflow-x: auto; padding: 12px; white-space: pre; }
        .guidance-message { white-space: pre-line; }
        ul { list-style: none; margin: 0; padding: 0; }
        li { border-top: 1px solid var(--divider-color); display: flex; flex-direction: column; gap: 5px; padding: 14px 0; }
        li:first-child { border-top: 0; padding-top: 0; }
        .wide { grid-column: 1 / -1; }
        a { color: var(--primary-color); text-decoration: none; }
        .error { color: var(--error-color); margin-top: 12px; }
        .dialog-backdrop { align-items: center; background: color-mix(in srgb, #000 45%, transparent); display: flex; inset: 0; justify-content: center; padding: 20px; position: fixed; z-index: 10; }
        .dialog { background: var(--card-background-color, var(--primary-background-color)); border-radius: 8px; max-width: 520px; padding: 24px; width: 100%; }
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
          <section class="wide guidance ${guidance?.actionable ? "warning" : "state"}">
            <h2>Guided Quirk setup</h2>
            <strong>${this._escape(guidance?.title || "Loading guidance...")}</strong>
            <pre>zha:
  custom_quirks_path: /config/zha_quirks/ezaiot/</pre>
            <p class="guidance-message">${this._escape(guidance?.message || "")}</p>
            <p class="muted" style="margin-top:12px">This setting is manual. After an update, Reconfigure or re-pair when guidance asks you to.</p>
          </section>
          <section>
            <h2>Supported devices</h2>
            <div class="metric">${status ? status.supported_count : "—"}</div>
            <p class="${status && status.supported_count > 0 ? "state" : "muted"}">${status && status.supported_count > 0 ? "Exact-match ZHA devices found" : "Rti-Tek eTRV-ZB01 exact matches only"}</p>
          </section>
          <section>
            <h2>Approved Quirk Release</h2>
            <p class="${release?.state === "update_available" ? "state" : "warning"}">${this._escape(release?.message || "Loading test Release status...")}</p>
            ${release?.test_mode ? "<p class=\"test-mode\">Unsigned test mode</p>" : ""}
            ${release?.available_version ? `<p class="muted">Installed: ${this._escape(release.installed_version || "none")} · Available: ${this._escape(release.available_version)}</p>` : ""}
            ${releaseNotes ? `<p class="muted" style="margin-top:12px">${releaseNotes}</p>` : ""}
            ${release?.restart_required ? "<p class=\"warning\" style=\"margin-top:12px\">Restart Home Assistant after deployment to load the Quirk.</p>" : ""}
            ${isAdmin ? `
              <div class="release-actions">
                <button data-release-action="ezaiot/check_release" ${actionInProgress ? "disabled" : ""}>Check approved Release</button>
                <button class="primary" data-release-action="ezaiot/install_release" ${!canInstall || actionInProgress ? "disabled" : ""}>Install approved Quirk</button>
                <button data-release-action="ezaiot/rollback_release" ${!hasBackup || actionInProgress ? "disabled" : ""}>Rollback</button>
              </div>` : ""}
          </section>
          <section class="wide">
            <h2>Compatibility</h2>
            <ul>${deviceContent}</ul>
          </section>
          <section class="wide">
            <h2>Diagnostics and help</h2>
            <p>Download the same redacted diagnostics used by Home Assistant before requesting support.</p>
            ${isAdmin ? `
              <div class="release-actions">
                <button data-diagnostics-action="download" ${this._diagnosticsAction ? "disabled" : ""}>Download ZHA diagnostics</button>
              </div>` : ""}
            <h2 style="margin-top:24px">Technical support</h2>
            <p><a href="mailto:${this._escape(support?.email || "support@ezaiot.com")}">${this._escape(support?.email || "support@ezaiot.com")}</a></p>
            ${support?.documentation_url ? `<p style="margin-top:12px"><a href="${this._escape(support.documentation_url)}" target="_blank" rel="noreferrer">Documentation</a></p>` : ""}
            <p class="muted" style="margin-top:12px">Tutorial and review links will appear here when configured.</p>
          </section>
        </div>
        ${onboarding?.show_completion ? `<div class="dialog-backdrop" role="dialog" aria-modal="true" aria-label="Setup complete"><div class="dialog"><h2>Setup complete</h2><p>The managed Quirk is active for a supported ZHA device.</p><p class="muted" style="margin-top:12px">Use Download ZHA diagnostics or Technical support if you need help. The review page is not available yet.</p><div class="release-actions"><button class="primary" data-dismiss-completion="true">Continue</button><button disabled>Review page coming soon</button></div></div></div>` : ""}
        ${this._error ? `<p class="error">${this._error}</p>` : ""}
      </main>
    `;
    this.shadowRoot.querySelector(".refresh")?.addEventListener("click", () => this._loadStatus(true));
    this.shadowRoot.querySelectorAll("[data-release-action]").forEach((button) => {
      button.addEventListener("click", () => {
        const type = button.dataset.releaseAction;
        const confirmation = type === "ezaiot/check_release"
          ? "Check the fixed approved Release source? No files will be changed during this check."
          : type === "ezaiot/install_release"
          ? "Install this approved Quirk Release? Only managed files in /config/zha_quirks/ezaiot/ will be replaced and one backup retained. Home Assistant must be restarted afterwards."
          : type === "ezaiot/rollback_release"
            ? "Restore the previous unsigned test Release? Home Assistant must be restarted afterwards."
            : null;
        this._runReleaseAction(type, confirmation);
      });
    });
    this.shadowRoot.querySelector("[data-diagnostics-action]")?.addEventListener(
      "click",
      () => this._downloadDiagnostics(),
    );
    this.shadowRoot.querySelector("[data-dismiss-completion]")?.addEventListener(
      "click",
      () => this._dismissCompletion(),
    );
  }
}

customElements.define("ezaiot-panel", EzaiotPanel);
