# Digital Humain — Developer Paper (Run Guide)

Short guide for developers: run instructions and where to find core components.

1. Project layout
-----------------
- Repository root — user-facing GUI scripts: `gui_main.py`, `gui_letta.py`
- `digital_humain/` — core package (agent, memory, vlm, tools, orchestration)
- `scripts/` — build and helper scripts
- `config/` — configuration and `config.yaml`
- `data/` — runtime data/artifacts (see `data/` in this repo)
- `docs/` — documentation

2. Quick run (developer)
------------------------
Create and activate a virtual environment, then install developer extras:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -e .[all]
python gui_main.py
```

3. Key developer pointers
-------------------------
- `digital_humain/core/agent.py`: BaseAgent and patterns (ReAct).  
- `digital_humain/core/engine.py`: Engine that orchestrates agent steps and handles cancellation.  
- `digital_humain/vlm/`: screen capture and GUI analysis utilities.  
- `digital_humain/memory/`: episodic & demonstration memory implementations.  
- `digital_humain/tools/`: tool interfaces and registration.

4. Build and test
-----------------
- Run tests: `pytest tests/ -q`
- Build exe (optional): `python scripts/build_exe.py`

5. Where to look for Letta-inspired features
--------------------------------------------
- `digital_humain/memory/` contains episodic and demonstration memory patterns influenced by Letta (core/persona separation).  
- `gui_letta.py` contains Letta-style GUI behaviors.

6. Notes
--------
Older, overlapping documents were archived to keep `docs/` focused. Check version history for previous contents if needed.
