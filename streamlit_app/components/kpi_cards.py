"""
kpi_cards.py
------------
Enterprise KPI card component for RetailPulse AI.
Renders clean, modern executive metrics with zero markdown escaping bugs.
"""

import textwrap
import streamlit as st


def render_kpi_card(
    title: str,
    value: str,
    subtext: str = "",
    delta: str = None,
    delta_type: str = "positive",
    icon_name: str = "trend"
):
    """
    Renders an enterprise-grade metric card with guaranteed clean HTML rendering.
    Uses st.html (or unindented markdown fallback) to avoid CommonMark code block bugs.
    """
    # Clean delta indicator
    delta_html = ""
    if delta:
        if delta_type == "positive":
            bg_color = "rgba(16, 185, 129, 0.12)"
            text_color = "#34D399"
            border_color = "rgba(16, 185, 129, 0.25)"
            arrow = "↑"
        elif delta_type == "negative":
            bg_color = "rgba(239, 68, 68, 0.12)"
            text_color = "#F87171"
            border_color = "rgba(239, 68, 68, 0.25)"
            arrow = "↓"
        else:
            bg_color = "rgba(148, 163, 184, 0.12)"
            text_color = "#94A3B8"
            border_color = "rgba(148, 163, 184, 0.2)"
            arrow = "•"

        delta_html = (
            f'<span style="display: inline-flex; align-items: center; gap: 4px; '
            f'background: {bg_color}; color: {text_color}; border: 1px solid {border_color}; '
            f'padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600;">'
            f'{arrow} {delta}'
            f'</span>'
        )

    # Subtext line
    subtext_html = ""
    if subtext:
        subtext_html = (
            f'<div style="color: #64748B; font-size: 12px; margin-top: 6px; font-weight: 400; '
            f'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">'
            f'{subtext}'
            f'</div>'
        )

    # Unindented card HTML
    card_html = (
        f'<div style="background: #111827; border: 1px solid rgba(255, 255, 255, 0.08); '
        f'border-radius: 12px; padding: 18px 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); '
        f'display: flex; flex-direction: column; justify-content: space-between; '
        f'min-height: 136px; box-sizing: border-box; margin-bottom: 14px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="color: #94A3B8; font-size: 11px; font-weight: 600; text-transform: uppercase; '
        f'letter-spacing: 0.06em;">{title}</span>'
        f'{delta_html}'
        f'</div>'
        f'<div style="color: #F8FAFC; font-size: 26px; font-weight: 700; letter-spacing: -0.02em; '
        f'line-height: 1.2;">'
        f'{value}'
        f'</div>'
        f'{subtext_html}'
        f'</div>'
    )

    if hasattr(st, "html"):
        st.html(card_html)
    else:
        st.markdown(textwrap.dedent(card_html).strip(), unsafe_allow_html=True)
