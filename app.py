"""
INSPIRATEK COMMAND CENTER
=========================
Streamlit dashboard for the Catalog Manager system.
Reads from PostgreSQL. Never processes data — only displays it.

Run: streamlit run dashboard/app.py --server.port 8501
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta

# CONFIG (replaces config.settings for Streamlit Cloud)
CFG = {
    "title": "Inspiratek Command Center",
    "refresh_interval_seconds": 300,
}

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title=CFG["title"],
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# DATABASE CONNECTION (cached)
# ============================================================================
@st.cache_resource
def get_db_connection():
    """Get database connection string from Streamlit secrets."""
    db = st.secrets["database"]
    return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['dbname']}"

@st.cache_data(ttl=CFG["refresh_interval_seconds"])
def query_db(sql: str, params: tuple = None) -> pd.DataFrame:
    """Execute query and return DataFrame. Cached for 5 minutes."""
    import psycopg
    conn = psycopg.connect(get_db_connection())
    try:
        df = pd.read_sql(sql, conn, params=params)
        return df
    finally:
        conn.close()

# ============================================================================
# DEMO MODE (when no DB connected)
# ============================================================================
def is_demo_mode():
    """Check if we should use demo data (no DB connection)."""
    try:
        import psycopg
        conn = psycopg.connect(get_db_connection())
        conn.close()
        return False
    except:
        return True

def get_demo_data():
    """Generate realistic demo data for all dashboard views."""
    import numpy as np
    np.random.seed(42)
    
    products = pd.DataFrame([
        {"asin": "B0D4QW1001", "brand": "DECOLURE", "product_title": "Velvet Quilt Set Queen", "variation_value": "Queen - Burgundy", "is_hero": True, "status": "active", "rating": 4.4, "review_count": 287, "open_alerts": 3, "critical_alerts": 1, "str_active": True, "str_price": 99.99, "current_price": 79.99, "str_discount_pct": 20.0, "seller_count": 1, "buybox_owner": "us", "fulfillable_qty": 342, "days_of_stock": 28},
        {"asin": "B0D4QW1002", "brand": "DECOLURE", "product_title": "Velvet Quilt Set King", "variation_value": "King - Navy", "is_hero": True, "status": "active", "rating": 4.3, "review_count": 195, "open_alerts": 2, "critical_alerts": 0, "str_active": True, "str_price": 109.99, "current_price": 89.99, "str_discount_pct": 18.2, "seller_count": 1, "buybox_owner": "us", "fulfillable_qty": 218, "days_of_stock": 22},
        {"asin": "B0D4QW1003", "brand": "DECOLURE", "product_title": "Bamboo Sheet Set Queen", "variation_value": "Queen - White", "is_hero": False, "status": "active", "rating": 4.5, "review_count": 512, "open_alerts": 1, "critical_alerts": 0, "str_active": False, "str_price": None, "current_price": 49.99, "str_discount_pct": None, "seller_count": 2, "buybox_owner": "us", "fulfillable_qty": 156, "days_of_stock": 12},
        {"asin": "B0D4QW1004", "brand": "DECOLURE", "product_title": "Satin Pillowcase Set", "variation_value": "Standard - Champagne", "is_hero": False, "status": "active", "rating": 4.6, "review_count": 823, "open_alerts": 0, "critical_alerts": 0, "str_active": True, "str_price": 24.99, "current_price": 18.99, "str_discount_pct": 24.0, "seller_count": 1, "buybox_owner": "us", "fulfillable_qty": 890, "days_of_stock": 45},
        {"asin": "B0D4QW1005", "brand": "SLEEPHORIA", "product_title": "Cooling Comforter Queen", "variation_value": "Queen - Grey", "is_hero": False, "status": "suppressed", "rating": 4.1, "review_count": 64, "open_alerts": 4, "critical_alerts": 2, "str_active": False, "str_price": None, "current_price": 69.99, "str_discount_pct": None, "seller_count": 1, "buybox_owner": "us", "fulfillable_qty": 87, "days_of_stock": 31},
    ])
    
    # Generate 30-day metrics
    dates = pd.date_range(end=date.today(), periods=30, freq='D')
    metrics_rows = []
    for _, prod in products.iterrows():
        base_sessions = np.random.randint(80, 300)
        base_units = int(base_sessions * np.random.uniform(0.08, 0.18))
        base_bsr = np.random.randint(5000, 80000)
        for i, d in enumerate(dates):
            sessions = max(10, int(base_sessions * np.random.uniform(0.7, 1.3)))
            units = max(1, int(base_units * np.random.uniform(0.5, 1.5)))
            bsr = max(1000, int(base_bsr * np.random.uniform(0.8, 1.2)))
            cvr = round(units / max(1, sessions) * 100, 1)
            revenue = round(units * float(prod['current_price']) * np.random.uniform(0.9, 1.1), 2)
            metrics_rows.append({
                "report_date": d.date(), "asin": prod['asin'], "brand": prod['brand'],
                "product_title": prod['product_title'], "sessions": sessions,
                "units_ordered": units, "revenue": revenue, "cvr": cvr, "bsr": bsr,
                "buybox_pct": np.random.uniform(85, 100) if prod['buybox_owner'] == 'us' else np.random.uniform(30, 60),
                "ad_spend": round(revenue * np.random.uniform(0.08, 0.20), 2),
                "effective_margin": round(np.random.uniform(18, 35), 1),
            })
    metrics = pd.DataFrame(metrics_rows)
    
    # Generate alerts
    alert_rows = []
    severities = ['critical', 'high', 'medium', 'info']
    sources = ['sellerise', 'custom', 'helium10', 'keepa']
    sample_alerts = [
        ("B0D4QW1005", "listing_suppressed", "listing", "critical", "sellerise", "Listing Suppressed: Incomplete product information", False),
        ("B0D4QW1001", "str_disappeared", "pricing", "critical", "custom", "STR pricing lost — was $99.99→$79.99", False),
        ("B0D4QW1001", "hijacker_detected", "listing", "critical", "sellerise", "New unauthorized seller: ZhongShan Trading at $54.99", False),
        ("B0D4QW1003", "keyword_deindexed", "keyword", "high", "helium10", "Lost indexing for 'bamboo sheets queen size'", False),
        ("B0D4QW1001", "review_negative", "review", "high", "sellerise", "1★ review: 'Color was nothing like the picture'", False),
        ("B0D4QW1002", "return_rate_spike", "returns", "high", "custom", "Queen Midgrey return rate 18.9% (2.1x baseline)", False),
        ("B0D4QW1005", "session_anomaly", "traffic", "critical", "custom", "Sessions 47% below same-day last week", False),
        ("B0D4QW1004", "badge_gained", "listing", "info", "helium10", "Amazon's Choice badge gained for 'satin pillowcase'", True),
        ("B0D4QW1001", "hijacker_removed", "listing", "info", "sellerise", "Unauthorized seller ZhongShan Trading removed", True),
        ("B0D4QW1001", "str_restored", "pricing", "info", "custom", "STR pricing restored: $99.99→$79.99 (20% off)", True),
        ("B0D4QW1002", "content_changed_images", "content", "high", "sellerise", "Main image changed on listing", False),
        ("B0D4QW1001", "pattern_detected", "intelligence", "critical", "custom", "LISTING MISMATCH CASCADE: content change → session drop → return spike", False),
        ("B0D4QW1003", "dimensions_changed", "fba_fees", "high", "sellerise", "Package dimensions changed — FBA fee may increase", False),
        ("B0D4QW1005", "margin_breach", "pricing", "high", "custom", "Effective margin 11.2% (below 15% floor)", False),
        ("B0D4QW1004", "reimbursement_found", "reimbursement", "info", "sellerise", "5 units reimbursable — estimated $94.95", True),
        ("B0D4QW1003", "inventory_velocity_low", "inventory", "medium", "custom", "12 days of stock remaining at current velocity", False),
    ]
    
    for i, (asin, atype, cat, sev, src, title, pos) in enumerate(sample_alerts):
        alert_rows.append({
            "id": i + 1,
            "alert_timestamp": datetime.now() - timedelta(days=np.random.randint(0, 14), hours=np.random.randint(0, 23)),
            "asin": asin, "alert_type": atype, "category": cat, "severity": sev,
            "source": src, "title": title, "is_positive": pos,
            "acknowledged": np.random.choice([True, False], p=[0.3, 0.7]),
            "resolved": pos,
        })
    alerts = pd.DataFrame(alert_rows).sort_values('alert_timestamp', ascending=False)
    
    # STR data
    str_data = products[['asin', 'brand', 'product_title', 'variation_value', 'str_active', 'str_price', 'current_price', 'str_discount_pct']].copy()
    str_data['check_date'] = date.today()
    str_data['str_days_active_30d'] = [28, 25, 0, 30, 0]
    
    # Return hotspots
    returns = pd.DataFrame([
        {"asin": "B0D4QW1001", "brand": "DECOLURE", "variation_label": "Queen - Midgrey", "return_rate_30d": 9.2, "return_rate_7d": 18.9, "units_sold_30d": 245, "units_returned_30d": 23, "top_reason_1": "Color not as expected", "top_reason_1_pct": 51.96, "is_spiking": True},
        {"asin": "B0D4QW1001", "brand": "DECOLURE", "variation_label": "Queen - Burgundy", "return_rate_30d": 6.1, "return_rate_7d": 5.8, "units_sold_30d": 312, "units_returned_30d": 19, "top_reason_1": "Wrong size", "top_reason_1_pct": 14.85, "is_spiking": False},
        {"asin": "B0D4QW1003", "brand": "DECOLURE", "variation_label": "Queen - White", "return_rate_30d": 4.3, "return_rate_7d": 4.1, "units_sold_30d": 198, "units_returned_30d": 9, "top_reason_1": "Quality not expected", "top_reason_1_pct": 33.3, "is_spiking": False},
        {"asin": "B0D4QW1005", "brand": "SLEEPHORIA", "variation_label": "Queen - Grey", "return_rate_30d": 7.8, "return_rate_7d": 12.4, "units_sold_30d": 64, "units_returned_30d": 5, "top_reason_1": "Too warm", "top_reason_1_pct": 40.0, "is_spiking": True},
    ])
    
    return products, metrics, alerts, str_data, returns

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .metric-card {
        background: white; border-radius: 12px; padding: 20px; margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #0D7377;
    }
    .metric-card.critical { border-left-color: #C0392B; }
    .metric-card.warning { border-left-color: #E67E22; }
    .metric-card.success { border-left-color: #27AE60; }
    .metric-value { font-size: 32px; font-weight: 700; color: #1B2A4A; }
    .metric-label { font-size: 13px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; }
    .alert-badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 11px; font-weight: 600; text-transform: uppercase;
    }
    .sev-critical { background: #FDEDEC; color: #C0392B; }
    .sev-high { background: #FEF5E7; color: #E67E22; }
    .sev-medium { background: #EBF5FB; color: #2980B9; }
    .sev-info { background: #EAFAF1; color: #27AE60; }
    .source-tag {
        display: inline-block; padding: 1px 8px; border-radius: 8px;
        font-size: 10px; font-weight: 500; margin-left: 6px;
    }
    .src-sellerise { background: #F5F3FF; color: #7C3AED; border: 1px solid #C4B5FD; }
    .src-custom { background: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA; }
    .src-helium10 { background: #F0FDFA; color: #0D7377; border: 1px solid #99F6E4; }
    .src-keepa { background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
    .str-active { color: #27AE60; font-weight: 600; }
    .str-inactive { color: #C0392B; font-weight: 600; }
    div[data-testid="stHeader"] { background: linear-gradient(135deg, #1B2A4A 0%, #0D7377 100%); }
    .status-active { color: #27AE60; font-weight: 600; }
    .status-suppressed { color: #C0392B; font-weight: 600; }
    .status-stranded { color: #E67E22; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING
# ============================================================================
DEMO = is_demo_mode()

if DEMO:
    products, metrics, alerts, str_data, returns = get_demo_data()
    st.sidebar.warning("📋 DEMO MODE — No database connected. Showing sample data.")
else:
    products = query_db("SELECT * FROM v_listing_health")
    metrics = query_db("SELECT * FROM v_metrics_trend")
    alerts = query_db("""
        SELECT al.*, p.brand, p.product_title 
        FROM alert_log al LEFT JOIN products p ON p.asin = al.asin 
        WHERE al.alert_timestamp > NOW() - INTERVAL '30 days'
        ORDER BY al.alert_timestamp DESC LIMIT 200
    """)
    str_data = query_db("SELECT * FROM v_str_dashboard")
    returns = query_db("SELECT * FROM v_return_hotspots")

# ============================================================================
# HEADER
# ============================================================================
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D7377 100%); padding: 24px 32px; border-radius: 12px; margin-bottom: 24px;">
    <h1 style="color: white; margin: 0; font-size: 28px;">🛡️ {CFG['title']}</h1>
    <p style="color: #94D3A2; margin: 4px 0 0 0; font-size: 14px;">
        Last updated: {datetime.now().strftime('%b %d, %Y %I:%M %p')} &nbsp;|&nbsp; 
        {len(products)} active listings &nbsp;|&nbsp;
        {'⚠️ DEMO MODE' if DEMO else '✅ Live Data'}
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# TABS
# ============================================================================
tab_dashboard, tab_alerts, tab_products, tab_str, tab_returns = st.tabs([
    "📊 Dashboard", "🔔 Alerts", "📦 Products", "💲 STR Monitor", "↩️ Returns"
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab_dashboard:
    # Traffic light summary
    unresolved = alerts[~alerts['is_positive'] & ~alerts['resolved']] if 'resolved' in alerts.columns else alerts[~alerts['is_positive']]
    critical_count = len(unresolved[unresolved['severity'] == 'critical'])
    high_count = len(unresolved[unresolved['severity'] == 'high'])
    
    active_count = len(products[products['status'] == 'active'])
    total_count = len(products)
    str_active_count = len(products[products['str_active'] == True])
    avg_rating = products['rating'].mean()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        card_class = "critical" if active_count < total_count else "success"
        st.markdown(f"""<div class="metric-card {card_class}">
            <div class="metric-label">Listing Health</div>
            <div class="metric-value">{active_count}/{total_count}</div>
            <div style="font-size:12px;color:#777;">Active listings</div>
        </div>""", unsafe_allow_html=True)
    
    with col2:
        bb_pct = products[products['buybox_owner'] == 'us'].shape[0] / max(1, len(products)) * 100
        card_class = "critical" if bb_pct < 80 else ("warning" if bb_pct < 95 else "success")
        st.markdown(f"""<div class="metric-card {card_class}">
            <div class="metric-label">Buy Box</div>
            <div class="metric-value">{bb_pct:.0f}%</div>
            <div style="font-size:12px;color:#777;">Owned</div>
        </div>""", unsafe_allow_html=True)
    
    with col3:
        card_class = "critical" if str_active_count < total_count * 0.5 else "success"
        st.markdown(f"""<div class="metric-card {card_class}">
            <div class="metric-label">STR Active</div>
            <div class="metric-value">{str_active_count}/{total_count}</div>
            <div style="font-size:12px;color:#777;">Strikethrough pricing</div>
        </div>""", unsafe_allow_html=True)
    
    with col4:
        card_class = "critical" if avg_rating < 4.0 else ("warning" if avg_rating < 4.3 else "success")
        st.markdown(f"""<div class="metric-card {card_class}">
            <div class="metric-label">Avg Rating</div>
            <div class="metric-value">{avg_rating:.1f}★</div>
            <div style="font-size:12px;color:#777;">Across {int(products['review_count'].sum())} reviews</div>
        </div>""", unsafe_allow_html=True)
    
    with col5:
        total_alerts = critical_count + high_count
        card_class = "critical" if critical_count > 0 else ("warning" if high_count > 0 else "success")
        st.markdown(f"""<div class="metric-card {card_class}">
            <div class="metric-label">Open Alerts</div>
            <div class="metric-value">{total_alerts}</div>
            <div style="font-size:12px;color:#777;">{critical_count} critical, {high_count} high</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Data source legend
    st.markdown("""
    <div style="display:flex; gap:16px; margin-bottom:16px; flex-wrap:wrap;">
        <span class="source-tag src-sellerise">🟣 Sellerise</span>
        <span class="source-tag src-custom">🟠 Custom (n8n/DB)</span>
        <span class="source-tag src-helium10">🔵 Helium 10</span>
        <span class="source-tag src-keepa">🟢 Keepa</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Product cards with sparklines
    st.subheader("Product Overview")
    
    for _, prod in products.iterrows():
        asin = prod['asin']
        prod_metrics = metrics[metrics['asin'] == asin].sort_values('report_date')
        prod_alerts = unresolved[unresolved['asin'] == asin]
        
        border_color = "#C0392B" if prod.get('critical_alerts', 0) > 0 else ("#E67E22" if len(prod_alerts) > 0 else "#27AE60")
        status_class = f"status-{prod['status']}"
        
        with st.container():
            col_info, col_chart, col_metrics, col_status = st.columns([3, 4, 3, 2])
            
            with col_info:
                st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding-left: 12px;">
                    <strong style="font-size: 15px;">{prod['brand']} — {prod.get('variation_value', '')}</strong><br>
                    <span style="font-size: 12px; color: #777;">{asin}</span><br>
                    <span class="{status_class}" style="font-size: 12px;">{prod['status'].upper()}</span>
                    &nbsp;|&nbsp; <span style="font-size: 12px;">{prod['rating']:.1f}★ ({prod['review_count']} reviews)</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_chart:
                if not prod_metrics.empty and 'revenue' in prod_metrics.columns:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=prod_metrics['report_date'], y=prod_metrics['revenue'],
                        mode='lines', fill='tozeroy', line=dict(color='#0D7377', width=2),
                        fillcolor='rgba(13,115,119,0.1)', name='Revenue'
                    ))
                    fig.update_layout(
                        height=80, margin=dict(l=0, r=0, t=0, b=0),
                        showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"spark_{asin}")
            
            with col_metrics:
                if not prod_metrics.empty:
                    latest = prod_metrics.iloc[-1]
                    rev_7d = prod_metrics.tail(7)['revenue'].sum()
                    units_7d = prod_metrics.tail(7)['units_ordered'].sum()
                    st.markdown(f"""
                    <div style="font-size: 13px;">
                        <strong>${rev_7d:,.0f}</strong> <span style="color:#777;">7d rev</span><br>
                        <strong>{units_7d}</strong> <span style="color:#777;">units (7d)</span><br>
                        <strong>{latest.get('bsr', 'N/A')}</strong> <span style="color:#777;">BSR</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_status:
                alert_count = len(prod_alerts)
                crit = prod.get('critical_alerts', 0)
                str_icon = "✅" if prod['str_active'] else "❌"
                st.markdown(f"""
                <div style="font-size: 13px; text-align: right;">
                    STR: {str_icon}<br>
                    {'🔴 ' + str(crit) + ' critical' if crit > 0 else ''} 
                    {'🟠 ' + str(alert_count) + ' open' if alert_count > 0 else '🟢 Clear'}<br>
                    📦 {prod.get('fulfillable_qty', 'N/A')} units ({prod.get('days_of_stock', '?')}d)
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 8px 0; border-color: #eee;'>", unsafe_allow_html=True)


# ============================================================================
# TAB 2: ALERTS
# ============================================================================
with tab_alerts:
    st.subheader("Alert Timeline")
    
    # Filters
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        asin_filter = st.selectbox("Product", ["All Products"] + sorted(products['asin'].unique().tolist()), key="alert_asin")
    with col_f2:
        sev_filter = st.multiselect("Severity", ["critical", "high", "medium", "info"], default=["critical", "high"], key="alert_sev")
    with col_f3:
        src_filter = st.multiselect("Source", sorted(alerts['source'].unique().tolist()), default=alerts['source'].unique().tolist(), key="alert_src")
    with col_f4:
        days_filter = st.slider("Days back", 1, 30, 14, key="alert_days")
    
    # Apply filters
    filtered = alerts.copy()
    if asin_filter != "All Products":
        filtered = filtered[filtered['asin'] == asin_filter]
    if sev_filter:
        filtered = filtered[filtered['severity'].isin(sev_filter)]
    if src_filter:
        filtered = filtered[filtered['source'].isin(src_filter)]
    cutoff = datetime.now() - timedelta(days=days_filter)
    filtered = filtered[filtered['alert_timestamp'] >= cutoff]
    
    # Metric chart with alert overlay (if single product selected)
    if asin_filter != "All Products":
        prod_m = metrics[metrics['asin'] == asin_filter].sort_values('report_date')
        if not prod_m.empty:
            metric_choice = st.radio("Metric", ["Revenue", "Sessions", "BSR", "CVR"], horizontal=True, key="chart_metric")
            metric_col = {"Revenue": "revenue", "Sessions": "sessions", "BSR": "bsr", "CVR": "cvr"}[metric_choice]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=prod_m['report_date'], y=prod_m[metric_col],
                mode='lines+markers', name=metric_choice,
                line=dict(color='#0D7377', width=2.5),
                marker=dict(size=5, color='#0D7377'),
                fill='tozeroy', fillcolor='rgba(13,115,119,0.08)',
            ))
            
            # Overlay alert markers
            for _, alert in filtered.iterrows():
                alert_date = alert['alert_timestamp']
                if isinstance(alert_date, datetime):
                    alert_date = alert_date.date()
                metric_val = prod_m[prod_m['report_date'] == alert_date]
                if not metric_val.empty:
                    y_val = metric_val[metric_col].values[0]
                    color = CFG['severity_colors'].get(alert['severity'], '#999')
                    symbol = "triangle-up" if alert['is_positive'] else "triangle-down"
                    fig.add_trace(go.Scatter(
                        x=[alert_date], y=[y_val],
                        mode='markers', marker=dict(size=14, color=color, symbol=symbol, line=dict(width=2, color='white')),
                        name=alert['alert_type'], text=[alert['title']],
                        hoverinfo='text', showlegend=False,
                    ))
            
            fig.update_layout(
                height=350, margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='white', plot_bgcolor='white',
                xaxis=dict(gridcolor='#f0f0f0'), yaxis=dict(gridcolor='#f0f0f0'),
                title=f"{metric_choice} — {asin_filter}",
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Alert list
    st.markdown(f"**{len(filtered)} alerts** in the last {days_filter} days")
    
    for _, alert in filtered.iterrows():
        sev = alert['severity']
        src = alert['source']
        sev_class = f"sev-{sev}"
        src_class = f"src-{src}"
        icon = "🟢" if alert['is_positive'] else {"critical": "🔴", "high": "🟠", "medium": "🔵", "info": "ℹ️"}.get(sev, "⚪")
        
        ts = alert['alert_timestamp']
        if isinstance(ts, datetime):
            time_str = ts.strftime('%b %d, %I:%M %p')
        else:
            time_str = str(ts)
        
        st.markdown(f"""
        <div style="background: white; border-radius: 8px; padding: 12px 16px; margin: 6px 0; 
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05); border-left: 3px solid {CFG['severity_colors'].get(sev, '#999')};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    {icon} <strong>{alert['title']}</strong>
                    <span class="alert-badge {sev_class}">{sev}</span>
                    <span class="source-tag {src_class}">{src}</span>
                </div>
                <span style="font-size: 12px; color: #999;">{time_str}</span>
            </div>
            <div style="font-size: 12px; color: #777; margin-top: 4px;">
                {alert['asin']} &nbsp;|&nbsp; {alert['category']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# TAB 3: PRODUCTS
# ============================================================================
with tab_products:
    st.subheader("Product Performance Grid")
    
    for _, prod in products.iterrows():
        asin = prod['asin']
        prod_m = metrics[metrics['asin'] == asin].sort_values('report_date')
        
        with st.expander(f"**{prod['brand']}** — {prod.get('product_title', '')} ({asin})", expanded=False):
            if not prod_m.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4], vertical_spacing=0.08)
                    fig.add_trace(go.Scatter(x=prod_m['report_date'], y=prod_m['revenue'], name='Revenue', line=dict(color='#0D7377', width=2), fill='tozeroy', fillcolor='rgba(13,115,119,0.08)'), row=1, col=1)
                    fig.add_trace(go.Bar(x=prod_m['report_date'], y=prod_m['units_ordered'], name='Units', marker_color='#2980B9', opacity=0.6), row=2, col=1)
                    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), showlegend=True, legend=dict(orientation="h", y=1.12), title="Revenue & Units")
                    st.plotly_chart(fig, use_container_width=True, key=f"prod_rev_{asin}")
                
                with col2:
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.5, 0.5], vertical_spacing=0.08)
                    fig.add_trace(go.Scatter(x=prod_m['report_date'], y=prod_m['sessions'], name='Sessions', line=dict(color='#E67E22', width=2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=prod_m['report_date'], y=prod_m['cvr'], name='CVR %', line=dict(color='#27AE60', width=2)), row=2, col=1)
                    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), showlegend=True, legend=dict(orientation="h", y=1.12), title="Sessions & CVR")
                    st.plotly_chart(fig, use_container_width=True, key=f"prod_sess_{asin}")


# ============================================================================
# TAB 4: STR MONITOR
# ============================================================================
with tab_str:
    st.subheader("Strikethrough Price Monitor")
    
    st.markdown("""
    <div style="background: #FEF5E7; border-left: 4px solid #E67E22; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
        <strong>Custom Pipeline:</strong> Keepa reference_price → n8n (every 6 hours) → PostgreSQL str_status → this display.
        No third-party tool monitors STR. This is 100% custom intelligence.
    </div>
    """, unsafe_allow_html=True)
    
    for _, row in products.iterrows():
        str_active = row.get('str_active', False)
        str_class = "str-active" if str_active else "str-inactive"
        str_icon = "✅ Active" if str_active else "❌ Inactive"
        
        price_display = ""
        if str_active and row.get('str_price'):
            price_display = f"<del>${row['str_price']:.2f}</del> → <strong>${row['current_price']:.2f}</strong> ({row.get('str_discount_pct', 0):.0f}% off)"
        elif row.get('current_price'):
            price_display = f"${row['current_price']:.2f} (no strikethrough)"
        
        st.markdown(f"""
        <div style="background: white; border-radius: 8px; padding: 16px; margin: 8px 0; 
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>{row['brand']} — {row.get('variation_value', row['asin'])}</strong><br>
                <span style="font-size: 12px; color: #777;">{row['asin']}</span>
            </div>
            <div style="text-align: center;">
                <span class="{str_class}" style="font-size: 18px;">{str_icon}</span><br>
                <span style="font-size: 14px;">{price_display}</span>
            </div>
            <div style="text-align: right; font-size: 12px; color: #777;">
                {row.get('str_days_active_30d', '?')} of 30 days active
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # STR Pipeline diagram
    st.markdown("---")
    st.markdown("**STR Detection Pipeline**")
    st.markdown("""
    ```
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  Keepa API   │───▶│ n8n Workflow  │───▶│  PostgreSQL  │───▶│ Alert Rules  │───▶│  This Panel  │
    │ reference_   │    │ Every 6 hrs  │    │  str_status  │    │ STR lost =   │    │ + Slack push │
    │ price field  │    │ Extract STR  │    │  table       │    │ CRITICAL     │    │ to Erik + AB │
    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
    ```
    """)


# ============================================================================
# TAB 5: RETURNS
# ============================================================================
with tab_returns:
    st.subheader("Return Rate Analysis")
    
    if not returns.empty:
        # Highlight spiking variations
        spiking = returns[returns['is_spiking'] == True]
        if not spiking.empty:
            st.markdown(f"""
            <div style="background: #FDEDEC; border-left: 4px solid #C0392B; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
                <strong>⚠️ {len(spiking)} variations spiking</strong> — 7-day return rate &gt; 2x baseline
            </div>
            """, unsafe_allow_html=True)
        
        # Return rate chart
        fig = go.Figure()
        for _, row in returns.iterrows():
            color = '#C0392B' if row['is_spiking'] else '#0D7377'
            fig.add_trace(go.Bar(
                x=[f"{row['brand']}\n{row['variation_label']}"],
                y=[row['return_rate_7d']],
                name=f"{row['variation_label']} (7d)",
                marker_color=color, opacity=0.8,
                text=[f"{row['return_rate_7d']}%"],
                textposition='outside',
            ))
        
        fig.add_hline(y=10, line_dash="dash", line_color="#C0392B", annotation_text="10% threshold")
        fig.update_layout(
            height=350, showlegend=False,
            title="7-Day Return Rates by Variation",
            yaxis_title="Return Rate %",
            paper_bgcolor='white', plot_bgcolor='white',
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detail table
        st.markdown("**Return Details by Variation**")
        for _, row in returns.iterrows():
            spike_icon = "🔴 SPIKING" if row['is_spiking'] else "🟢 Normal"
            st.markdown(f"""
            <div style="background: white; border-radius: 8px; padding: 12px 16px; margin: 6px 0;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.05); border-left: 3px solid {'#C0392B' if row['is_spiking'] else '#27AE60'};">
                <strong>{row['brand']} — {row['variation_label']}</strong> ({row['asin']}) &nbsp; {spike_icon}<br>
                <span style="font-size: 13px;">
                    30-day rate: <strong>{row['return_rate_30d']}%</strong> &nbsp;|&nbsp;
                    7-day rate: <strong style="color: {'#C0392B' if row['is_spiking'] else '#333'}">{row['return_rate_7d']}%</strong> &nbsp;|&nbsp;
                    {row['units_returned_30d']}/{row['units_sold_30d']} units returned<br>
                    Top reason: <strong>{row['top_reason_1']}</strong> ({row['top_reason_1_pct']}%)
                </span>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #999; font-size: 12px; padding: 8px;">
    {CFG['title']} v1.0 &nbsp;|&nbsp; Data sources: Sellerise · Helium 10 · Keepa · SP-API · Custom n8n &nbsp;|&nbsp; 
    Auto-refresh: every {CFG['refresh_interval_seconds']//60} minutes
</div>
""", unsafe_allow_html=True)
