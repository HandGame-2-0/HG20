from dataclasses import dataclass
from enum import Enum

class ThemeId(str ,Enum):
    NAVY = "navy"
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
    # Optional finer-grained tokens used by the game screens (header/HUD bars,
    # hover, selection, focus...). None = derived from the base tokens above,
    # so a palette only has to set the ones it wants to differ.
    heading: str | None = None
    background_end: str | None = None  # bottom of the app background gradient
    surface_alt: str | None = None  # hover, gameplay area
    highlight: str | None = None  # selected tile / option
    accent_hover: str | None = None
    accent_soft: str | None = None  # thin accent strips and hover borders
    accent_disabled: str | None = None
    button_text: str | None = None  # text on secondary (surface) buttons
    border_strong: str | None = None  # inputs and buttons
    bar: str | None = None  # header bar, HUD, preview panel, results card
    bar_raised: str | None = None  # buttons sitting on a bar
    bar_text: str | None = None
    bar_text_muted: str | None = None
    bar_accent: str | None = None
    focus: str | None = None
    focus_on_bar: str | None = None
    disabled_text: str | None = None
    disabled_surface: str | None = None
    disabled_border: str | None = None
    error_on_bar: str | None = None
    backdrop: str | None = None  # dimmed layer behind modals

    def as_template_mapping(self) -> dict[str, str]:
        bar = self.bar or self.accent
        bar_text = self.bar_text or self.accent_text
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
            "heading": self.heading or self.text,
            "background_end": self.background_end or self.background,
            "surface_alt": self.surface_alt or self.background,
            "highlight": self.highlight or self.background,
            "accent_hover": self.accent_hover or self.accent,
            "accent_soft": self.accent_soft or self.accent,
            "accent_disabled": self.accent_disabled or self.border,
            "button_text": self.button_text or self.text,
            "border_strong": self.border_strong or self.border,
            "bar": bar,
            "bar_raised": self.bar_raised or bar,
            "bar_text": bar_text,
            "bar_text_muted": self.bar_text_muted or bar_text,
            "bar_accent": self.bar_accent or bar_text,
            "focus": self.focus or self.accent,
            "focus_on_bar": self.focus_on_bar or bar_text,
            "disabled_text": self.disabled_text or self.text_muted,
            "disabled_surface": self.disabled_surface or self.background,
            "disabled_border": self.disabled_border or self.border,
            "error_on_bar": self.error_on_bar or bar_text,
            "backdrop": self.backdrop or "rgba(0, 0, 0, 150)",
        }

NAVY = ThemeToken(
    name="Granatowy",
    background="#F4F6FA",
    surface="#FFFFFF",
    text="#1B2433",
    text_muted="#3E4C63",
    accent="#0B2545",
    accent_text="#FFFFFF",
    error="#DC3220",
    success="#009E73",
    border="#D3DCE8",
    font_family="Inter",
    heading="#0B2545",
    background_end="#DDEFFC",
    surface_alt="#EEF7FD",
    highlight="#D6ECFB",
    accent_hover="#1D4E89",
    accent_soft="#5FA8E0",
    accent_disabled="#A7B6CB",
    button_text="#13315C",
    border_strong="#C3CFDF",
    bar="#0B2545",
    bar_raised="#13315C",
    bar_text="#FFFFFF",
    bar_text_muted="#A9D6F5",
    bar_accent="#5FA8E0",
    focus="#2F80ED",
    focus_on_bar="#FFFFFF",
    disabled_text="#8A9AB0",
    disabled_surface="#EEF2F7",
    disabled_border="#E1E7EF",
    error_on_bar="#FF6B6B",
    backdrop="rgba(11, 37, 69, 170)",
)

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
    ThemeId.NAVY: NAVY,
    ThemeId.LIGHT: LIGHT, 
    ThemeId.DARK: DARK,
    ThemeId.PROTANOPIA: PROTANOPIA,
    ThemeId.DEUTERANOPIA: DEUTERANOPIA,
    ThemeId.TRITANOPIA: TRITANOPIA,
    ThemeId.MONOCHROME: MONOCHROME
    }
DEFAULT_THEME = ThemeId.NAVY


def get_tokens(theme_id: ThemeId) -> ThemeToken:
    return PALETTES[theme_id]