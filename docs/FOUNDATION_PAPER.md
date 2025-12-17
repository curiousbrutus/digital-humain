# Digital Humain — Foundation Paper

Authors: Project Team
Date: 2025-12-16

Abstract
--------
Digital Humain is a modular, self-hosted agentic AI framework for desktop automation that combines visual understanding (VLM) with robust multi-agent orchestration. This paper documents the core architecture, memory subsystems, tool model, safety design, and recommended deployment patterns. It is written as a concise scientific/developer reference to guide future maintenance and research work.

1. Introduction
---------------
Digital Humain provides a ReAct-style agent pipeline with vision-driven action capabilities. The system focuses on: (1) reliable desktop GUI automation, (2) episodic and demonstration memory for learning, and (3) flexible LLM provider integration (local Ollama or cloud OpenRouter/Letta).

2. Architecture Overview
------------------------
- Core package `digital_humain`: agent core, orchestration, tools, VLM, memory, and utils.
- Agent execution: `AgentEngine` drives `BaseAgent` implementations (e.g., `DesktopAutomationAgent`) using a graph-based reasoning/execution pipeline.
- Vision: `vlm` captures screenshots, analyzes UI, and exposes `GUIActions` for safe interaction.
- Tools: modular `BaseTool` implementations are registered in a `ToolRegistry` and available to agents.
- Providers: `OllamaProvider`, `OpenRouterProvider`, and `LettaProvider` provide unified LLM interfaces.

3. Memory Subsystems
--------------------
- Demonstration memory: records user actions for playback and learning.
- Episodic memory: short-term episodes are stored and summarized for retrieval.
- Archival memory (optional): long-term facts, compacted and searchable.
- Memory design principle: keep code under `digital_humain/memory/` and runtime data under `data/` (git-ignored).

4. Safety & Controls
--------------------
- Visual safety pause, overlay indicators, and a `cancel_event` pattern for graceful task aborts.
- Recording and dry-run modes for demonstration playback.
- Default conservative action pacing and explicit user confirmations in high-risk flows.

5. Deployment & Packaging
-------------------------
- Install via `pip install -e .[all]` for full dev+gui+build environment.
- Build standalone using `scripts/build_exe.py` (PyInstaller spec `DigitalHumain.spec`).
- Runtime directories: `data/episodic_memory/`, `data/demonstrations/`, `data/screenshots/`, `data/logs/`.

6. Research Directions
----------------------
- Improve memory summarization and retrieval precision.  
- Integrate model-agnostic token budgeting and planning utilities.  
- Explore multi-agent coordination strategies with stronger failure isolation.

7. Conclusion
-------------
This foundation paper should serve as a technical reference. For the canonical, repo-accurate overview (what/why/how and current filenames), see `docs/START_HERE.md`.

References
----------
- Letta / MemGPT concepts (influence): memory + core/persona separation.  
- Agent S2 style orchestration: graph-based reasoning and action loops.
