from dataclasses import dataclass
from enum import Enum

class ThemeId(str ,Enum):
    LIGHT = "light"
    DARK = "dark"
    PROTANOPIA = "protanopia"
    DEUTERANOPIA = "deuteranopia"
    TRITANOPIA = "tritanopia"
    MONOCHROME = "monochrome"
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
    background="#F8F9FA",
    surface="#ffffff",
    text="#212529",
    text_muted="#6b7280",
    accent="#005AB5",
    accent_text="#ffffff",
    error="#DC3220",
    success="#009E73",
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
PROTANOPIA = ThemeToken(
    name="Protanopia",
    background="#F7F7F7",
    surface="#ffffff",
    text="#1A1A1A",
    text_muted="#5C5C5C",
    accent="#0072B2",
    accent_text="#ffffff",
    error="#E69F00",
    success="#56B4E9",
    border="#B0B0B0",
)
DEUTERANOPIA = ThemeToken(
    name="Deuteranopia",
    background="#F7F7F5",
    surface="#ffffff",
    text="#1A1A1A",
    text_muted="#5C5C5C",
    accent="#0072B2",
    accent_text="#ffffff",
    error="#D55E00",
    success="#56B4E9",
    border="#B0B0B0",
)
TRITANOPIA = ThemeToken(
    name="Tritanopia",
    background="#F6F4F2",
    surface="#ffffff",
    text="#1A1A1A",
    text_muted="#5C5C5C",
    accent="#CC79A7",
    accent_text="#ffffff",
    error="#D55E00",
    success="#009E73",
    border="#C4B8B0",
)

MONOCHROME = ThemeToken(
    name="Monochromatyzm",
    background="#F5F5F5",
    surface="#ffffff",
    text="#111111",
    text_muted="#616161",
    accent="#222222",
    accent_text="#ffffff",
    error="#000000",
    success="#6E6E6E",
    border="#9E9E9E",
)

PALETTES = {
    ThemeId.LIGHT: LIGHT, 
    ThemeId.DARK: DARK,
    ThemeId.PROTANOPIA: PROTANOPIA,
    ThemeId.DEUTERANOPIA: DEUTERANOPIA,
    ThemeId.TRITANOPIA: TRITANOPIA,
    ThemeId.MONOCHROME: MONOCHROME
    }
DEFAULT_THEME = ThemeId.LIGHT


def get_tokens(theme_id: ThemeId) -> ThemeToken:
    return PALETTES[theme_id]