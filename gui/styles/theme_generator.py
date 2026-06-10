"""
Generate the complete QSS stylesheet from TDS tokens.
"""
from gui.styles.design_system import TDS


def generate_stylesheet() -> str:
    T = TDS
    return f"""
/* ════════════════════════════════════════════════════════
   Esperanto Language Suite — TEKIRA Design System
   Light Editorial Theme · Apple-Inspired
   ════════════════════════════════════════════════════════ */

/* ── Global ─────────────────────────────────────────── */
QMainWindow {{
    background-color: {T.BG_SECONDARY};
}}
QWidget {{
    font-family: {T.FONT_FAMILY};
    color: {T.TEXT_PRIMARY};
    font-size: {T.FONT_BODY}px;
}}
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    background: {T.BORDER_COLOR};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ── Splash Screen ──────────────────────────────────── */
#SplashScreen {{
    background-color: {T.BG_PRIMARY};
}}
#SplashTitle {{
    font-family: {T.FONT_FAMILY_SERIF};
    font-size: 80px;
    font-weight: 800;
    color: #111111;
    letter-spacing: -2px;
}}
#SplashProgress {{
    background-color: {T.BG_TERTIARY};
    border-radius: 2px;
    max-height: 4px;
}}
#SplashProgress::chunk {{
    background-color: {T.GOLD};
    border-radius: 2px;
}}

/* ── Sidebar ────────────────────────────────────────── */
#Sidebar {{
    background-color: {T.BG_SIDEBAR};
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}}
#SidebarBrand {{
    font-family: {T.FONT_FAMILY_SERIF};
    font-size: {T.FONT_H3}px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 2.0px;
}}
#SidebarSearch {{
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #AEAEB2;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-size: {T.FONT_BODY - 1}px;
}}
#SidebarSearch:hover {{
    background-color: rgba(255, 255, 255, 0.09);
    border-color: rgba(255, 255, 255, 0.15);
    color: #FFFFFF;
}}
#SidebarBtn {{
    text-align: left;
    padding: 10px 14px;
    background-color: transparent;
    color: #AEAEB2;
    border: none;
    border-radius: {T.RADIUS_SM}px;
    font-size: {T.FONT_BODY}px;
    font-weight: 500;
}}
#SidebarBtn:hover {{
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
}}
#SidebarBtnActive {{
    text-align: left;
    padding: 10px 14px;
    background-color: rgba(255, 255, 255, 0.15);
    color: #FFFFFF;
    border: none;
    border-radius: {T.RADIUS_SM}px;
    font-size: {T.FONT_BODY}px;
    font-weight: 600;
}}
#SidebarToggle {{
    background-color: transparent;
    border: none;
    color: #AEAEB2;
    font-size: 18px;
    border-radius: 6px;
    padding: 4px;
}}
#SidebarToggle:hover {{
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
}}
#SidebarProfile {{
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: {T.RADIUS_MD}px;
    padding: 10px;
    margin-top: 10px;
}}
#SidebarAvatar {{
    background-color: {T.GOLD};
    color: #FFFFFF;
    border-radius: 16px;
    font-weight: bold;
    font-size: {T.FONT_BODY}px;
}}
#SidebarUsername {{
    color: #FFFFFF;
    font-weight: 600;
    font-size: {T.FONT_BODY - 1}px;
}}
#SidebarUserRole {{
    color: #8E8E93;
    font-size: {T.FONT_SMALL}px;
}}

/* ── Hero Section ───────────────────────────────────── */
#HeroSection {{
    background-color: {T.BG_PRIMARY};
    border-radius: {T.RADIUS_LG}px;
    border: 1px solid {T.BORDER_COLOR};
    padding: {T.SPACE_XL}px;
}}
#HeroTitle {{
    font-family: {T.FONT_FAMILY_SERIF};
    font-size: {T.FONT_H1}px;
    font-weight: 700;
    color: {T.TEXT_PRIMARY};
    letter-spacing: -0.3px;
}}
#HeroSubtitle {{
    font-size: {T.FONT_BODY}px;
    color: {T.TEXT_SECONDARY};
}}
#HeroGold {{
    color: {T.GOLD};
    font-weight: 600;
}}

/* ── Metric Cards ───────────────────────────────────── */
#MetricCard {{
    background-color: {T.BG_PRIMARY};
    border-radius: {T.RADIUS_MD}px;
    border: none;
    padding: {T.SPACE_LG}px;
}}
#MetricCard:hover {{
    background-color: {T.BG_PRIMARY};
}}
#MetricLabel {{
    color: {T.TEXT_SECONDARY};
    font-size: {T.FONT_CAPTION}px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
#MetricValue {{
    color: {T.TEXT_PRIMARY};
    font-size: {T.FONT_H1}px;
    font-weight: 800;
}}
#MetricDesc {{
    color: {T.GOLD};
    font-size: {T.FONT_SMALL}px;
    font-weight: 500;
}}

/* ── Document Cards ─────────────────────────────────── */
#DocumentCard {{
    background-color: {T.BG_PRIMARY};
    border-radius: {T.RADIUS_MD}px;
    border: none;
}}
#DocumentCard:hover {{
    border: none;
}}
#CardTitle {{
    font-size: {T.FONT_BODY}px;
    font-weight: 600;
    color: {T.TEXT_PRIMARY};
}}
#CardStatus {{
    font-size: {T.FONT_CAPTION}px;
    font-weight: 500;
}}
#CardProgress {{
    background-color: {T.BG_TERTIARY};
    border-radius: 2px;
    max-height: 4px;
}}
#CardProgress::chunk {{
    background-color: {T.GOLD};
    border-radius: 2px;
}}

/* ── Drop Area ──────────────────────────────────────── */
#DropArea {{
    border: 2px dashed rgba(0, 0, 0, 0.05);
    border-radius: {T.RADIUS_MD}px;
    background-color: {T.BG_PRIMARY};
    color: {T.TEXT_TERTIARY};
    padding: {T.SPACE_XL}px;
    font-size: {T.FONT_BODY}px;
}}
#DropArea:hover {{
    border-color: {T.GOLD};
    color: {T.GOLD};
    background-color: {T.GOLD_SUBTLE};
}}

/* ── Text Input ─────────────────────────────────────── */
#TextInput {{
    background-color: {T.BG_PRIMARY};
    border: none;
    border-radius: {T.RADIUS_MD}px;
    padding: {T.SPACE_MD}px;
    color: {T.TEXT_PRIMARY};
    font-size: {T.FONT_BODY}px;
}}
#TextInput:focus {{
    background-color: {T.BG_PRIMARY};
}}

/* ── Review Panel ───────────────────────────────────── */
#ReviewCard {{
    background-color: {T.BG_PRIMARY};
    border-radius: {T.RADIUS_XL}px;
    border: none;
    padding: {T.SPACE_XXL}px;
}}
#ReviewContext {{
    font-size: {T.FONT_H3}px;
    color: {T.TEXT_TERTIARY};
    line-height: 1.6;
}}
#ReviewTarget {{
    font-family: {T.FONT_FAMILY_SERIF};
    font-size: 46px;
    font-weight: 800;
    color: {T.TEXT_PRIMARY};
    letter-spacing: -2px;
}}
#ExplanationBox {{
    background-color: {T.GOLD_SUBTLE};
    border-left: 4px solid {T.GOLD};
    border-radius: 4px;
    padding: {T.SPACE_MD}px;
}}
#ExplanationText {{
    color: {T.GOLD};
    font-size: {T.FONT_BODY}px;
    font-weight: 500;
}}

/* ── Buttons ────────────────────────────────────────── */
#PrimaryBtn {{
    background-color: {T.GOLD};
    color: {T.TEXT_INVERSE};
    border: none;
    border-radius: {T.RADIUS_SM}px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: {T.FONT_BODY}px;
}}
#PrimaryBtn:hover {{
    background-color: {T.GOLD_LIGHT};
}}
#SecondaryBtn {{
    background-color: transparent;
    color: {T.TEXT_SECONDARY};
    border: 1px solid {T.BORDER_COLOR};
    border-radius: {T.RADIUS_SM}px;
    padding: 10px 24px;
    font-weight: 500;
    font-size: {T.FONT_BODY}px;
}}
#SecondaryBtn:hover {{
    background-color: rgba(0, 0, 0, 0.03);
    color: {T.TEXT_PRIMARY};
    border-color: {T.TEXT_TERTIARY};
}}
#CandidateBtn {{
    background-color: {T.BG_PRIMARY};
    color: {T.TEXT_PRIMARY};
    border: 1px solid {T.BORDER_COLOR};
    border-radius: {T.RADIUS_MD}px;
    padding: 16px 24px;
    font-size: {T.FONT_H3}px;
    font-weight: 600;
}}
#CandidateBtn:hover {{
    border-color: {T.GOLD};
    background-color: {T.GOLD_SUBTLE};
    color: {T.GOLD};
}}

/* ── Section Labels ─────────────────────────────────── */
#SectionLabel {{
    font-size: {T.FONT_CAPTION}px;
    font-weight: 700;
    color: {T.TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Empty State ────────────────────────────────────── */
#EmptyState {{
    color: {T.TEXT_TERTIARY};
    font-size: {T.FONT_BODY}px;
}}
"""
