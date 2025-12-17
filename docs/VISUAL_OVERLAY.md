# Visual Overlay (Action Feedback)

Digital Humain can optionally render an on-screen overlay to provide **real-time visual feedback** about what the agent is doing (e.g., clicks, typing locations, or action targets).

## Purpose

Desktop automation is hard to trust without feedback. The overlay is intended to:
- make actions observable and auditable during a run,
- reduce operator anxiety and improve safety,
- help debugging when actions miss the intended UI element.

## Implementation Location

- Overlay module: `digital_humain/vlm/overlay.py`

## Notes

- The overlay is a safety/usability feature; it does not replace sandboxing.
- If overlay is enabled, it should not block input or interfere with automation timing.

## Related

- GUI action primitives: `digital_humain/vlm/actions.py`
- Security guidance: `docs/SECURITY.md`
