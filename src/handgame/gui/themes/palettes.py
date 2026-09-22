from dataclasses import dataclass
from enum import Enum

class ThemeId(str ,Enum):
    LIGHT = "light"
    DARK = "dark"

@dataclass(frozen=True)
class ThemeToken:
    name: str
    background: str
    surface: str
    text: str
    text_muted: str
    accent: str
    accent_text: str
    error: str
    success: str
    border: str
    font_family: str = "Segoe UI"
    font_size_px: int = 14

    def as_template_mapping(self) -> dict[str, str]:
        return {
            "name": self.name,
            "background": self.background,
            "surface": self.surface,
            "text": self.text,
            "text_muted": self.text_muted,
            "accent": self.accent,
            "accent_text": self.accent_text,
            "error": self.error,
            "success": self.success,
            "border": self.border,
            "font_family": self.font_family,
            "font_size_px": str(self.font_size_px),
        }

LIGHT = ThemeToken(
    name="Jasny",
    background="#f4f6f8",
    surface="#ffffff",
    text="#1f2933",
    text_muted="#6b7280",
    accent="#2563eb",
    accent_text="#ffffff",
    error="#c0392b",
    success="#15803d",
    border="#d1d5db",
)

DARK = ThemeToken(
    name="Ciemny",
    background="#111827",
    surface="#1f2937",
    text="#f9fafb",
    text_muted="#9ca3af",
    accent="#3b82f6",
    accent_text="#ffffff",
    error="#f87171",
    success="#4ade80",
    border="#374151",
)

PALETTES = {ThemeId.LIGHT: LIGHT, ThemeId.DARK: DARK}
DEFAULT_THEME = ThemeId.LIGHT


def get_tokens(theme_id: ThemeId) -> ThemeToken:
    return PALETTES[theme_id]