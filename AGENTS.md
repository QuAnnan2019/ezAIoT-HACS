# ezAIoT Development Guide

## Purpose

This repository contains the `ezaiot` Home Assistant custom integration. The
first release is a local-only compatibility and diagnostic helper for the
Rti-Tek `eTRV-ZB01` ZHA device.

## Boundaries

- Keep platform code in `custom_components/ezaiot/` and tests in `tests/`.
- Match supported hardware by exact manufacturer and model values only.
- Do not read or expose device names, identifiers, IEEE addresses, IP data,
  credentials, tokens, entity IDs, or raw attributes in diagnostics.
- Do not modify ZHA, YAML, Zigbee2MQTT, or other integrations.

## Verification

Use the repository virtual environment for commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check custom_components tests
```

Inspect the diff and report the executed validation and any remaining manual
Home Assistant verification before completion.

## Commit Rules

- Keep every commit small, cohesive, and independently reviewable.
- One commit must implement exactly one functional change or one focused fix.
- Do not combine multiple features, refactors, formatting, dependency updates,
  generated files, or unrelated cleanup in the same commit.
- Stage only files required by that commit. Leave unrelated working-tree and
  staged changes untouched.
- Write every commit subject and body in English.
- Keep the subject to one line of at most 70 characters.
- If a body is needed, put one blank line after the subject and keep every body
  line in English and at most 70 characters.

## Local Development Documentation

- Use the local `docs/` directory to record requirements, constraints,
  decisions, progress, verification results, and blockers.
- Update the relevant document before starting substantial work and after a
  meaningful implementation or verification change.
- Treat these documents as local development records only. Never stage,
  commit, or push any file below `docs/`.
- Keep requirements and constraints factual. Record assumptions and unresolved
  choices explicitly instead of presenting them as confirmed decisions.
