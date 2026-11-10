"""
Design-Tokens: die EINE Stelle für Farben, Radien, Schriften und Abstände.

App (Qt), Zeichnungen (Matplotlib) und Animationen (Manim) lesen alle von hier.
Vorlage ist eine unabhängige Analyse des ElevenLabs-Designsystems
(getdesign.md, DESIGN.md): heller Off-White-Canvas, warme Tinte, weisse Karten
mit Hairline, Pillen-Buttons, keine gesättigte Akzentfarbe. Die Display-Schrift
Waldenburg gibt es nicht frei, Ersatz ist EB Garamond Light. Schriftdateien
liegen nicht im Repo; fehlt eine Schrift, greift der Rückfall.

Das Modul braucht weder Qt noch Matplotlib noch Manim.
"""

from __future__ import annotations

# --- Rohfarben ----------------------------------------------------------
INK = "#292524"             # primär: Tinte
INK_DEEP = "#0c0a09"        # Hover/Press, Dunkelfläche
BODY = "#4e4e4e"
MUTED = "#777169"
MUTED_SOFT = "#a8a29e"
HAIRLINE = "#e7e5e4"
HAIRLINE_STRONG = "#d6d3d1"
CANVAS = "#f5f5f5"
CARD = "#ffffff"
SURFACE = "#f0efed"
DARK_CARD = "#1c1917"

# Pastell nur als Atmosphäre (Orbs) und als zarte Flächen
MINT, PEACH, LAVENDER, SKY, ROSE = "#a7e5d3", "#f4c5a8", "#c8b8e0", "#a8c8e8", "#e8b8c4"
ORBS = (MINT, PEACH, LAVENDER, SKY, ROSE)

# Bedeutung: Wahr/Falsch. Textton etwas dunkler als der Ton der Vorlage,
# damit er auf der Pastellfläche genug Kontrast hat (>= 4.5:1).
SUCCESS, ERROR = "#16a34a", "#dc2626"
SUCCESS_FILL, ERROR_FILL = "#15803d", "#b91c1c"     # Flächen mit weisser Schrift (Kontrast >= 4.5:1)

# --- Radien, Abstände, Zeiten --------------------------------------------
R_CARD, R_INPUT, R_PILL = 16, 8, 20      # Pille: mind. halbe Höhe (Qt kennt kein 999px)
SPACE = 8                   # Grundraster; Seitenabstände sind Vielfache davon
SHADOW_HOVER = (0, 4, 16, 10)           # x, y, blur, Alpha (0..255) = rgba(0,0,0,.04)
T_FAST, T_PAGE = 150, 220               # ms

# --- Schriften (erste gefundene gewinnt) ---------------------------------
UI_FONTS = ["Inter", "SF Pro Text", ".AppleSystemUIFont", "Helvetica Neue",
            "Segoe UI Variable Text", "Segoe UI", "DejaVu Sans"]
DISPLAY_FONTS = ["EB Garamond", "Cormorant Garamond", "New York", "Iowan Old Style",
                 "Baskerville", "Georgia", "Times New Roman", "DejaVu Serif"]
MONO_FONTS = ["SF Mono", "Menlo", "Cascadia Mono", "Consolas", "DejaVu Sans Mono"]
LETTER_SPACING = 0.2        # px, Fliesstext leicht geweitet

# --- App-Palette (Schlüssel wie bisher in dmatkit_qt.T) -------------------
APP_LIGHT = dict(
    bg=CANVAS, nav=CANVAS, card=CARD, text=INK_DEEP, sec=BODY, ter=MUTED,
    line=HAIRLINE_STRONG, hair=HAIRLINE, fill=SURFACE, fill2="#fafafa",
    seg=CARD, blue=INK, blue_hi=INK_DEEP, blue_soft=SURFACE, on_blue="#ffffff",
    green="#15803d", green_soft="#e1f3ea", red="#b91c1c", red_soft="#fbe8e6",
    amber="#9a5b0a", amber_soft="#fdefdc", flash="#fdefdc",
    entry=CARD, hi_soft="#e2edf8", scroll=HAIRLINE_STRONG, shadow=SHADOW_HOVER[3], dark=False)

APP_DARK = dict(
    bg=INK_DEEP, nav=INK_DEEP, card=DARK_CARD, text="#fafaf9", sec="#d6d3d1",
    ter=MUTED_SOFT, line="#44403c", hair="#292524", fill="#292524", fill2="#171412",
    seg="#44403c", blue="#fafaf9", blue_hi="#ffffff", blue_soft="#292524", on_blue=INK_DEEP,
    green="#4ade80", green_soft="#14301f", red="#f87171", red_soft="#3b1b1a",
    amber="#fbbf24", amber_soft="#3a2c12", flash="#3a2c12",
    entry=DARK_CARD, hi_soft="#1e3347", scroll="#44403c", shadow=0, dark=True)

# --- Zeichnungen (Matplotlib) ---------------------------------------------
# accent = Tinte (keine Signalfarbe); red/good tragen Bedeutung (falsch/wahr).
PLOT_LIGHT = dict(
    dark=False, bg=CARD, fg=INK, muted=MUTED, grid=HAIRLINE, accent=INK, red=ERROR_FILL,
    soft=SURFACE, tint="#e3f4ee", good=SUCCESS_FILL, on_color="#ffffff",
    series=[INK, "#5b87b5", "#c27a52", "#4f9c82", "#8e7bb5", "#b5707f"])
PLOT_DARK = dict(
    dark=True, bg=DARK_CARD, fg="#fafaf9", muted=MUTED_SOFT, grid="#2e2a27",
    accent="#fafaf9", red="#e0807a", soft="#292524", tint="#1f3a33", good="#5eb98a",
    on_color=INK_DEEP,
    series=["#fafaf9", "#8fb4dc", "#e2a07c", "#7fcfb4", "#b9a6dc", "#dc9aa8"])

# --- Animation (Manim) ------------------------------------------------------
ANIM_LIGHT = dict(background=CANVAS, text=INK, muted=MUTED, accent=INK,
                  good=SUCCESS, bad=ERROR, soft=HAIRLINE_STRONG)
ANIM_DARK = dict(background=INK_DEEP, text="#fafaf9", muted=MUTED_SOFT, accent="#fafaf9",
                 good="#4ade80", bad="#f87171", soft="#44403c")
