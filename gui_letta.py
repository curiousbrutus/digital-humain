"""Thin entrypoint for the Letta-style GUI.

This file exists to provide a stable, discoverable launch command:
    python gui_letta.py

The main implementation lives in `letta_gui.py`.
"""

from __future__ import annotations

import tkinter as tk

from letta_gui import LettaStyleGUI


def main() -> None:
    root = tk.Tk()
    LettaStyleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
