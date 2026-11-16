"""
charts.py
---------
Enterprise Plotly visualizations for RetailPulse AI.
Styled with a modern, high-contrast dark theme (Stripe/Linear inspired):
- Monthly revenue trend with MoM growth overlay
- Regional revenue donut & breakdown
- Top 10 products by revenue & volume
- Category revenue distribution
- Quantity sold analysis
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

THEME_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", color="#E2E8F0"),
    margin=dict(l=15, r=15, t=35, b=15),
    hoverlabel=dict(
        bgcolor="#1E293B",
        bordercolor="rgba(255, 255, 255, 0.12)",
        font=dict(family="Inter, sans-serif", size=12, color="#F8FAFC")
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(color="#94A3B8", size=11)
    )
)

COLOR_PALETTE = ["#3B82F6", "#10B981", "#6366F1", "#F59E0B", "#06B6D4", "#EC4899", "#8B5CF6"]


def plot_monthly_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly Revenue Trend with MoM Growth overlay."""
    fig = go.Figure()

    # Revenue Bar
    fig.add_trace(go.Bar(
        x=df["year_month"],
        y=df["total_revenue"],
        name="Revenue ($)",
        marker=dict(
            color="#3B82F6",
            opacity=0.9,
            line=dict(color="#2563EB", width=1)
        ),
        hovertemplate="<b>%{x}</b><br>Revenue: <b>$%{y:,.2f}</b><extra></extra>"
    ))

    # Trend Line
    fig.add_trace(go.Scatter(
        x=df["year_month"],
        y=df["total_revenue"],
        name="Trend",
        mode="lines+markers",
        line=dict(color="#10B981", width=2.5, shape="spline"),
        marker=dict(size=7, color="#10B981", line=dict(color="#FFFFFF", width=1.5)),
        hovertemplate="<b>%{x}</b><br>Trend: <b>$%{y:,.2f}</b><extra></extra>"
    ))

    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text="Monthly Revenue Trend (2024)", font=dict(size=14, color="#F1F5F9", weight=600)),
        xaxis=dict(showgrid=False, title="", color="#94A3B8", tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title="Revenue ($)", color="#94A3B8", tickfont=dict(size=11)),
        hovermode="x unified",
        bargap=0.3
    )
    return fig


def plot_regional_distribution(df: pd.DataFrame) -> go.Figure:
    """Donut chart for Regional Revenue breakdown."""
    fig = go.Figure(data=[go.Pie(
        labels=df["region"],
        values=df["total_revenue"],
        hole=0.62,
        marker=dict(colors=COLOR_PALETTE),
        textinfo="label+percent",
        textfont=dict(color="#FFFFFF", size=11),
        hovertemplate="<b>%{label} Region</b><br>Revenue: <b>$%{value:,.2f}</b><br>Share: <b>%{percent}</b><extra></extra>"
    )])

    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text="Revenue by Region", font=dict(size=14, color="#F1F5F9", weight=600)),
        showlegend=True
    )
    return fig


def plot_top_products(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    """Horizontal bar chart for Top N Products by Revenue."""
    top_df = df.sort_values(by="total_revenue", ascending=True).tail(limit)

    fig = go.Figure(go.Bar(
        x=top_df["total_revenue"],
        y=top_df["product_name"],
        orientation="h",
        marker=dict(
            color="#3B82F6",
            opacity=0.85,
            line=dict(color="#60A5FA", width=1)
        ),
        hovertemplate="<b>%{y}</b><br>Revenue: <b>$%{x:,.2f}</b><extra></extra>"
    ))

    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text=f"Top {limit} Products by Revenue", font=dict(size=14, color="#F1F5F9", weight=600)),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title="Revenue ($)", color="#94A3B8", tickfont=dict(size=11)),
        yaxis=dict(showgrid=False, title="", color="#CBD5E1", tickfont=dict(size=11))
    )
    return fig


def plot_category_breakdown(df: pd.DataFrame) -> go.Figure:
    """Category Revenue & Units breakdown bar chart."""
    cat_df = df.groupby("category").agg({
        "total_revenue": "sum",
        "total_quantity_sold": "sum"
    }).reset_index().sort_values(by="total_revenue", ascending=False)

    fig = px.bar(
        cat_df,
        x="category",
        y="total_revenue",
        color="category",
        color_discrete_sequence=COLOR_PALETTE,
        text=cat_df["total_revenue"].apply(lambda x: f"${x:,.0f}"),
        hover_data={"total_quantity_sold": True, "total_revenue": ":$,.2f"}
    )

    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text="Category-Wise Revenue", font=dict(size=14, color="#F1F5F9", weight=600)),
        xaxis=dict(showgrid=False, title="", color="#94A3B8", tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title="Revenue ($)", color="#94A3B8", tickfont=dict(size=11)),
        showlegend=False
    )
    return fig


def plot_volume_analysis(df: pd.DataFrame) -> go.Figure:
    """Sales Quantity Volume per Product."""
    vol_df = df.sort_values(by="total_units_sold", ascending=True).tail(10)

    fig = go.Figure(go.Bar(
        x=vol_df["total_units_sold"],
        y=vol_df["product_name"],
        orientation="h",
        marker=dict(color="#10B981", opacity=0.85, line=dict(color="#34D399", width=1)),
        hovertemplate="<b>%{y}</b><br>Units Sold: <b>%{x:,}</b><extra></extra>"
    ))

    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text="Top Products by Sales Volume (Units)", font=dict(size=14, color="#F1F5F9", weight=600)),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title="Units Sold", color="#94A3B8", tickfont=dict(size=11)),
        yaxis=dict(showgrid=False, title="", color="#CBD5E1", tickfont=dict(size=11))
    )
    return fig


def plot_mom_growth(df: pd.DataFrame) -> go.Figure:
    """Month-over-Month Revenue Growth Percentage."""
    fig = go.Figure()

    colors = ["#10B981" if val >= 0 else "#EF4444" for val in df["mom_growth_pct"].fillna(0)]

    fig.add_trace(go.Bar(
        x=df["year_month"],
        y=df["mom_growth_pct"].fillna(0),
        name="MoM Growth %",
        marker=dict(color=colors, opacity=0.85),
        hovertemplate="<b>%{x}</b><br>Growth: <b>%{y:.2f}%</b><extra></extra>"
    ))

    fig.update_layout(
        **THEME_LAYOUT,
        title=dict(text="Month-over-Month Revenue Growth (%)", font=dict(size=14, color="#F1F5F9", weight=600)),
        xaxis=dict(showgrid=False, title="", color="#94A3B8", tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title="Growth (%)", color="#94A3B8", tickfont=dict(size=11)),
        showlegend=False
    )
    return fig
