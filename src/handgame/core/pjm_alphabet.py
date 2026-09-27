"""PJM finger-alphabet vocabulary shared by recognition, games and tools.

Lives in ``core`` so minigames can use it without importing ``recognition``.
"""

from __future__ import annotations

# Letters shown with a single static hand shape (no movement), i.e. the ones a
# per-frame classifier can recognise. Dynamic letters (Ą, Ć, CH, CZ, Ł, ...)
# need a sequence model and are out of scope for now.
STATIC_LETTERS: tuple[str, ...] = (
    "A",
    "B",
    "C",
    "E",
    "I",
    "L",
    "M",
    "N",
    "O",
    "P",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "Y",
)
