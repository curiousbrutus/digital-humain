# Prompt Pack for Expert Reviews

Use these with Gemini Deep Research (or similar). Always attach both PROJECT_REPORT.md and co-expert-recommendations.md for full context.

## Quick Context Snippet (paste first)
Digital Humain is a privacy-first desktop automation agent using LangGraph state machines + ReAct. It automates GUIs with PyAutoGUI + OCR, supports local LLMs (Ollama) and cloud (OpenRouter/Letta), and ships as a standalone Windows .exe. Vision is placeholder (OCR-only). Known gaps: no sandboxing, limited error recovery, prone to reasoning loops, VLM not grounded. Goal: production-grade reliability, strong security, and VLM grounding.

## Prompts

### 1) Architecture & Control-Flow
Analyze the LangGraph + ReAct design for long-horizon desktop automation. Should we adopt hierarchical planning (planner + worker) with milestone checkpoints? What graph patterns (ToolException node, recovery edges, checkpointing) prevent loops and enable resumption? Compare against AutoGen/CrewAI for this use case.

### 2) VLM Strategy
Recommend a VLM plan for GUI grounding. Evaluate LLaVA 1.6, Qwen2-VL (quantized), and GPT-4V trade-offs: Accuracy@IoU, latency on consumer GPUs, and privacy. Propose a hybrid local+cloud policy for pixel-accurate clicks. Include quantization settings and minimum VRAM.

### 3) Reliability & Loop Busting
Design a failure-handling pattern: explicit ToolException routing, exponential backoff, observe/verify assertions after actions, and cache reuse for identical screens. Provide concrete LangGraph node/edge patterns and termination criteria to stop infinite observe/reason cycles.

### 4) Security & Isolation
Propose sandboxing for desktop automation: Windows Sandbox/VM vs. Docker+gVisor. Define least-privilege setup, allowlists, and prompt-injection defenses (instructional prevention + input separation). How to audit actions without leaking secrets?

### 5) Performance & Inference
Given sequential ReAct latency, suggest optimizations: vLLM/SGLang, KV-cache tuning, speculative decoding, and 4/8-bit quantization. Prioritize by ROI on a single-GPU Windows host. Include target p95 latency per reasoning step.

### 6) Roadmap Prioritization (3-6-12 months)
Prioritize security hardening, hierarchical planning, VLM grounding, and hybrid inference. Produce a quarter-by-quarter plan with acceptance tests (e.g., Accuracy@IoU ≥0.5 on top-10 UI actions, zero infinite-loop incidents in 100-run stress test).

### 7) Market & Positioning
Assess differentiation vs. UiPath/Automation Anywhere and proprietary agents (Claude Computer Use, GPT-4o). Identify best-fit verticals for privacy-first, on-prem automation (healthcare, finance, gov). Recommend pricing/licensing and community growth moves.

### 8) Benchmarking Plan
Define an evaluation harness for GUI automation: datasets, click accuracy metrics, loop incidence rate, task success rate, and recovery effectiveness. Include CI-friendly mocks for PyAutoGUI and vision.

### 9) Human-in-the-Loop
Design HITL checkpoints for destructive actions (delete/send). How to prompt for confirmation, pause/resume, and log for audit?

### 10) Migration Guidance
If LangGraph is retained, outline how to modularize VLM backends. If replaced, propose a migration plan to alternative orchestrators without losing checkpointing and recovery semantics.
