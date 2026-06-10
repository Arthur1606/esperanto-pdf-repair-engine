"""
TEKIRA Design System (TDS)
--------------------------
Centralized visual language for Esperanto Language Suite.
All visual tokens live here. No magic numbers in components.
"""


class TDS:
    """TEKIRA Design System tokens."""

    # ── Brand ──────────────────────────────────────────────
    BRAND_NAME = "Esperanto Language Suite"
    BRAND_SUBTITLE = "powered by TEKIRA"

    # ── Palette: Light Editorial ──────────────────────────
    BG_PRIMARY = "#FFFFFF"          # Pure white canvas
    BG_SECONDARY = "#F5F5F7"        # Apple warm gray
    BG_TERTIARY = "#E8E8ED"         # Subtle dividers
    BG_CARD = "#FFFFFF"             # Cards on gray bg
    BG_SIDEBAR = "#F5F5F7"

    TEXT_PRIMARY = "#1D1D1F"        # Apple near-black
    TEXT_SECONDARY = "#6E6E73"      # Apple secondary
    TEXT_TERTIARY = "#AEAEB2"       # Placeholders
    TEXT_INVERSE = "#FFFFFF"

    # TEKIRA Gold – elegant, not flashy
    GOLD = "#C9A227"
    GOLD_LIGHT = "#D4AF37"
    GOLD_SUBTLE = "rgba(201, 162, 39, 0.08)"
    GOLD_BORDER = "rgba(201, 162, 39, 0.25)"

    ACCENT = "#007AFF"              # Apple blue for links
    SUCCESS = "#34C759"
    WARNING = "#FF9F0A"
    DANGER = "#FF3B30"

    # ── Borders & Shadows ─────────────────────────────────
    BORDER_COLOR = "#E5E5EA"
    BORDER_SUBTLE = "#F0F0F5"
    SHADOW_CARD = "rgba(0, 0, 0, 0.04)"
    SHADOW_ELEVATED = "rgba(0, 0, 0, 0.08)"

    # ── Spacing (px) ──────────────────────────────────────
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 16
    SPACE_LG = 24
    SPACE_XL = 32
    SPACE_XXL = 48

    # ── Radii ─────────────────────────────────────────────
    RADIUS_SM = 8
    RADIUS_MD = 12
    RADIUS_LG = 16
    RADIUS_XL = 20

    # ── Animation ─────────────────────────────────────────
    ANIM_FAST = 150       # ms
    ANIM_NORMAL = 250
    ANIM_SLOW = 400
    ANIM_SPLASH = 600

    # ── Typography (sizes in px) ──────────────────────────
    FONT_FAMILY = '-apple-system, "SF Pro Display", "SF Pro Text", "Helvetica Neue", "Segoe UI", Roboto, Arial, sans-serif'
    FONT_HERO = 34
    FONT_H1 = 28
    FONT_H2 = 22
    FONT_H3 = 17
    FONT_BODY = 15
    FONT_CAPTION = 13
    FONT_SMALL = 11
