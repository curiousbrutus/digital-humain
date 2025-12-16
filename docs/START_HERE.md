# Digital Humain — Canonical Overview (Start Here)

**Last updated**: 2025-12-16  
**Scope**: This document is the single source of truth for: what Digital Humain is, why it exists, what is implemented today, and how to extend it safely.

---

## 1) Problem Statement

Modern enterprises (healthcare/HBYS, accounting, quality/compliance) still rely on **desktop applications** where automation is expensive (UI changes, lack of APIs, brittle macros). At the same time, many organizations require **data sovereignty**: sensitive screen contents, credentials, and patient/financial records must not be sent to external providers.

Digital Humain addresses this by building a **self-hosted desktop automation agent** that can:
- perceive the desktop (screen capture + OCR/VLM),
- reason in multi-step loops (ReAct),
- act via GUI primitives (mouse/keyboard automation),
- coordinate multiple roles (planner/executor/analyzer),
- learn from experience (episodic memory) and from user demonstrations (record/replay).

---

## 2) Project History (What Happened)

This repository evolved through a sequence of practical constraints common to enterprise desktop automation:

- **Initial constraint**: target systems are often *desktop-only* (no reliable APIs), so automation must operate via screen + input events.
- **Reliability constraint**: long-horizon tasks require structured loops (observe → decide → act) with cancellation, retries, and verification.
- **Privacy constraint**: organizations often cannot send screen contents to external LLM/VLM endpoints, so local-first inference is required.

As a result, Digital Humain converged on:
- A **ReAct-style agent loop** plus orchestration patterns for multi-step task execution.
- A **tool boundary** (explicit tool calls) to keep actions auditable and testable.
- Two operator-facing GUIs (`gui_main.py` and `gui_letta.py`) for running tasks and observing/controlling execution.
- **Learning components** (episodic + demonstration memory) to reduce repeated manual instruction.

---

## 3) Project Goals and Non-Goals

### Goals
- **Privacy-first execution**: enable local inference (Ollama) as a default posture.
- **Reliable long-horizon automation**: support multi-step tasks with retry/guardrails.
- **Extensibility**: make it easy to add tools, agents, memory backends, and perception.
- **Operational usability**: provide a GUI to run tasks, observe progress, and stop safely.

### Non-goals (current scope)
- Replacing full RPA suites (UiPath/AA) feature-for-feature.
- Full “computer-use” grounding with guaranteed pixel-accurate click selection under all UI changes.
- Running untrusted automation without sandboxing (sandboxing is recommended; see docs/SECURITY.md).

---

## 4) What Exists Today (Implemented Capabilities)

### 3.1 Core Agent Loop (ReAct)
- The base pattern is implemented in the core engine and agents:
  - `digital_humain/core/agent.py`
  - `digital_humain/core/engine.py`
  - `digital_humain/agents/automation_agent.py`

**Conceptual loop:** Observe → Reason → Act → Decide/Continue.

### 3.2 Perception (Screen)
- `digital_humain/vlm/screen_analyzer.py` performs screen capture and OCR fallback.
- A true VLM pathway is intended/optional depending on provider, hardware, and policy.

### 3.3 Action Execution (GUI)
- `digital_humain/vlm/actions.py` provides primitives (click, type, press key, scroll, etc.).
- `digital_humain/vlm/overlay.py` provides visual feedback overlay support.

### 3.4 Tool System
- Tools are registered and executed via:
  - `digital_humain/tools/base.py`
  - `digital_humain/tools/file_tools.py`

### 3.5 Multi-agent Coordination (Letta-inspired)
- Coordinated task decomposition and shared memory live under:
  - `digital_humain/orchestration/coordinator.py`
  - `digital_humain/orchestration/registry.py`
  - `digital_humain/orchestration/memory.py`

### 3.6 Memory and Learning
- Demonstration recording/replay:
  - `digital_humain/memory/demonstration.py`
- Episodic memory + summarization:
  - `digital_humain/memory/episodic.py`

Runtime data is stored on disk as folders next to the repo (default relative paths are `./demonstrations` and `./episodic_memory`).
This repository also includes a `data/` directory layout used for examples and collected artifacts.

---

## 5) Repository Map (Ground Truth)

Top-level entry points:
- `gui_main.py` — primary GUI
- `gui_letta.py` — Letta-style GUI variant
- `scripts/build_exe.py` — build script for packaging (PyInstaller)

Core library:
- `digital_humain/` — agents, orchestration, tools, perception, memory

Configuration:
- `config/config.yaml`

Runtime data:
- `data/` (expected to be git-ignored in production)

Tests:
- `tests/unit/`, `tests/integration/`, `tests/e2e/`

---

## 6) System Model (How Components Interact)

**Primary flow:**
1. A user provides a task (GUI or programmatic call).
2. The engine builds/executes a step graph (LangGraph pattern).
3. The agent observes (screen/context), reasons (LLM), then acts (GUI/tool).
4. Memory is updated (episodic/demonstration) depending on configuration.
5. The run terminates on completion criteria or a safety stop/cancel.

**High-level diagram:**

```
User / GUI
   │
   ▼
Agent Engine (LangGraph)
   │
   ├─► LLM Provider (Ollama/OpenRouter/Letta)
   │
   ├─► Perception (ScreenAnalyzer: capture/OCR/VLM)
   │
   ├─► Action Execution (GUIActions + optional Overlay)
   │
   ├─► Tools (ToolRegistry: file/system helpers)
   │
   └─► Memory (Episodic + Demonstrations)
```

---

## 7) How to Run (Operator Checklist)

### 6.1 Install
- Follow the repository root guide: `README.md` and `INSTALLATION.md`.

### 6.2 Launch the GUIs
- Standard GUI: `python gui_main.py`
- Letta-style GUI: `python gui_letta.py`

### 6.3 Run tests
- Unit tests: `pytest tests/unit/`
- Full suite: `pytest tests/`

### 6.4 Build a Windows executable
- Run: `python scripts/build_exe.py`

---

## 8) Extending the System (Developer Actions)

### Add a new tool
1. Create a tool under `digital_humain/tools/` extending `BaseTool`.
2. Register it in the tool registry where agents are assembled.
3. Add unit tests under `tests/unit/`.

### Add a new agent
1. Create an agent in `digital_humain/agents/` extending the base agent interface.
2. Decide whether it is standalone or orchestrated via the coordinator.
3. Add tests for decision logic and safe failure paths.

### Improve perception
1. Extend `ScreenAnalyzer` to support a chosen VLM provider.
2. Ensure that screenshots and extracted text are handled with privacy policy in mind.
3. Add regression tests (mocked) and a manual validation playbook.

---

## 9) Safety, Security, and Operational Constraints

Desktop automation is inherently high-risk because actions affect the real system.

Minimum safety requirements:
- Keep a user-visible stop/cancel mechanism.
- Prefer allowlists for dangerous operations (app launch, file deletion, network).
- Avoid storing secrets in memory logs.

See `docs/SECURITY.md` for sandboxing, prompt-injection defense, and auditing guidance.

---

## 10) Roadmap (What is Aimed)

Near-term (stability):
- Strengthen recovery patterns and loop-busting in the execution graph.
- Improve action verification (post-action checks, screen re-observe assertions).

Mid-term (grounding):
- Add a robust VLM backend for UI element grounding and click targeting.
- Build a repeatable benchmarking harness for GUI tasks.

Long-term (learning):
- Semantic retrieval (embeddings) for episodic memory.
- Adaptive replays that tolerate minor UI shifts.

---

## 11) How an AI Contributor Should Work

If you are an AI agent improving this repo:
- Treat `docs/START_HERE.md` as canonical. If other docs disagree, update them or mark them historical.
- Prefer changing code + tests together.
- Keep privacy-first defaults.
- Verify that referenced filenames/paths exist before documenting them.

Recommended workflow:
1. Reproduce or describe the issue clearly.
2. Identify the smallest safe change.
3. Add/adjust tests.
4. Update docs only when the behavior changed.

---

## 12) Navigation (Where to Read Next)

- Architecture: `docs/ARCHITECTURE.md`
- Technical report: `docs/PROJECT_REPORT.md`
- Security: `docs/SECURITY.md`
- Memory & learning: `docs/MEMORY_FEATURES.md`
- Letta GUI (UI-level documentation): `docs/LETTA_GUI.md`
