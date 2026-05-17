import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import warnings
warnings.filterwarnings("ignore")


st.set_page_config(
    page_title="Kitchen P&L",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f5f6fa; }

    [data-testid="stSidebar"] {
        background-color: #1e1e2e;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: #aaaaaa !important;
        font-size: 12px;
    }
    [data-testid="stSidebar"] .stMultiSelect span {
        background-color: #3a3a5c !important;
        color: #ffffff !important;
    }

    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #6c63ff;
    }
    .kpi-val {
    font-size: 22px;
    font-weight: 700;
    color: #2d2d2d;
    font-family: monospace;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
    .kpi-label {
        font-size: 11px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 6px;
    }

    .note {
        background: #fff8e1;
        border-left: 4px solid #f0a500;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        color: #7a6000;
        font-size: 13px;
        margin-bottom: 14px;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 10px;
        padding: 4px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        color: #666 !important;
        font-weight: 500;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background: #6c63ff !important;
        color: white !important;
    }

    /* section label in sidebar */
    .sidebar-section {
        color: #aaaaaa;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 14px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data():
    df = pd.read_excel("Kittchen_PNL_Data.xlsx")
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]
    df.rename(columns={
        "ZONE_MAPPING":   "ZONE",
        "KITCHEN_EBITDA": "EBITDA",
        "IDEAL_FOOD_COST": "FOOD_COST",
        "EBITDA_CATEGORY": "EBITDA_CATEGORY",
    }, inplace=True)

    df["GM%"] = (df["GROSS_MARGIN"] / df["NET_REVENUE"] * 100).round(2)
    df["EBITDA%"] = (df["EBITDA"] / df["NET_REVENUE"] * 100).round(2)
    df["VARIANCE%"] = (df["VARIANCE"] / df["NET_REVENUE"] * 100).round(4)
    df["CM"] = df["GROSS_MARGIN"]
    df["CM%"] = df["GM%"]

    bins = [0, 2, 3, 5, 999]
    bucket_names = ["(a) Var < 2%", "(b) Var 2% to 3%",
                    "(c) Var 3% to 5%", "(d) Var > 5%"]
    df["VAR_BUCKET"] = pd.cut(df["VARIANCE%"], bins=bins, labels=bucket_names)

    month_seq = ["Oct-2023", "Nov-2023", "Dec-2023",
                 "Jan-2024", "Feb-2024", "Mar-2024"]
    df["MONTH"] = pd.Categorical(
        df["MONTH"], categories=month_seq, ordered=True)
    df.sort_values("MONTH", inplace=True)
    return df


def to_inr(val):
    if pd.isna(val):
        return "—"
    if abs(val) >= 1e7:
        return f"₹{val/1e7:.2f}Cr"
    if abs(val) >= 1e5:
        return f"₹{val/1e5:.2f}L"
    return f"₹{val:,.0f}"


def to_pct(val):
    return "—" if pd.isna(val) else f"{val:.1f}%"


def safe_format(df_in):
    # handles both old and new pandas (applymap vs map)
    def fn(x): return f"{x:.2f}%" if pd.notna(x) else "—"
    try:
        return df_in.applymap(fn)
    except AttributeError:
        return df_in.map(fn)


df = load_data()

month_list = list(df["MONTH"].cat.categories)
rev_cohort_order = ["INR 20 to 30 lacs",
                    "INR 30 to 40 lacs", "More than 40 lacs"]
var_buckets = ["(a) Var < 2%", "(b) Var 2% to 3%",
               "(c) Var 3% to 5%", "(d) Var > 5%"]

all_cities = sorted(df["CITY"].unique())
all_zones = sorted(df["ZONE"].unique())
all_stores = sorted(df["STORE"].unique())
all_rev = sorted(df["REVENUE_COHORT"].unique())
all_cm = sorted(df["CM_COHORT"].unique())
all_ecat = sorted(df["EBITDA_CATEGORY"].unique())
all_ecoh = sorted(df["EBITDA_COHORT"].unique())


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍳 Kitchen P&L")
    st.markdown("---")

    st.markdown("**⏱ TIME**")
    sel_months = st.multiselect("Select Month", month_list)

    st.markdown("**📍 LOCATION**")
    sel_cities = st.multiselect("Select City",   all_cities)
    sel_zones = st.multiselect("Select Zone",   all_zones)
    sel_stores = st.multiselect("Select Store",  all_stores)
    sel_status = st.multiselect("Select Status", ["Active", "Inactive"])

    st.markdown("**📊 COHORTS**")
    sel_rev = st.multiselect("Select Revenue Cohort",  all_rev)
    sel_cm = st.multiselect("Select CM Cohort",       all_cm)
    sel_ecat = st.multiselect("Select EBITDA Category", all_ecat)
    sel_ecoh = st.multiselect("Select EBITDA Cohort",   all_ecoh)

    st.markdown("**🎚 RANGES**")
    rev_range = st.slider("Net Revenue (₹)",
                          int(df["NET_REVENUE"].min()), int(
                              df["NET_REVENUE"].max()),
                          (int(df["NET_REVENUE"].min()), int(df["NET_REVENUE"].max())), step=50000)

    ebitda_range = st.slider("EBITDA (₹)",
                             int(df["EBITDA"].min()), int(df["EBITDA"].max()),
                             (int(df["EBITDA"].min()), int(df["EBITDA"].max())), step=10000)

    cm_range = st.slider("CM / Gross Margin (₹)",
                         int(df["CM"].min()), int(df["CM"].max()),
                         (int(df["CM"].min()), int(df["CM"].max())), step=50000)

    st.markdown("---")
    st.caption("Cache refreshes every 5 min.")
# ── FILTER ────────────────────────────────────────────────────────────────────


def filter_df(data):
    d = data.copy()
    if sel_months:
        d = d[d["MONTH"].isin(sel_months)]
    if sel_cities:
        d = d[d["CITY"].isin(sel_cities)]
    if sel_zones:
        d = d[d["ZONE"].isin(sel_zones)]
    if sel_stores:
        d = d[d["STORE"].isin(sel_stores)]
    if sel_status:
        d = d[d["STATUS"].isin(sel_status)]
    if sel_rev:
        d = d[d["REVENUE_COHORT"].isin(sel_rev)]
    if sel_cm:
        d = d[d["CM_COHORT"].isin(sel_cm)]
    if sel_ecat:
        d = d[d["EBITDA_CATEGORY"].isin(sel_ecat)]
    if sel_ecoh:
        d = d[d["EBITDA_COHORT"].isin(sel_ecoh)]
    d = d[
        d["NET_REVENUE"].between(*rev_range) &
        d["EBITDA"].between(*ebitda_range) &
        d["CM"].between(*cm_range)
    ]
    return d


fdf = filter_df(df)


# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "  📋 Kitchen P&L  ",
    "  📉 Variance P&L  ",
    "  💡 Insights  "
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 📋 Kitchen Snapshot")
    st.caption("Store-level P&L. Use the sidebar to filter.")

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, val in [
        (c1, "Total Revenue", to_inr(fdf["NET_REVENUE"].sum())),
        (c2, "Total EBITDA",  to_inr(fdf["EBITDA"].sum())),
        (c3, "Avg GM%",       to_pct(fdf["GM%"].mean())),
        (c4, "Avg EBITDA%",   to_pct(fdf["EBITDA%"].mean())),
        (c5, "Stores",        str(fdf["STORE"].nunique())),
    ]:
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-val">{val}</div>'
                f'<div class="kpi-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("")
    st.markdown("#### Store × Month Table")
    st.markdown(
        '<div class="note">⚠️ No CM column in raw data — Gross Margin used as proxy.</div>',
        unsafe_allow_html=True
    )

    if fdf.empty:
        st.warning("No data matches the current filters.")
    else:
        active_months = [m for m in month_list if m in fdf["MONTH"].values]
        rows = []
        for store, grp in fdf.groupby("STORE", sort=True):
            row = {"Store": store}
            for m in active_months:
                mg = grp[grp["MONTH"] == m]
                if mg.empty:
                    row[f"{m} Rev"] = "—"
                    row[f"{m} GM%"] = "—"
                    row[f"{m} CM%"] = "—"
                    row[f"{m} EBITDA"] = "—"
                    row[f"{m} EBITDA%"] = "—"
                else:
                    row[f"{m} Rev"] = to_inr(mg["NET_REVENUE"].sum())
                    row[f"{m} GM%"] = to_pct(mg["GM%"].mean())
                    row[f"{m} CM%"] = to_pct(mg["CM%"].mean())
                    row[f"{m} EBITDA"] = to_inr(mg["EBITDA"].sum())
                    row[f"{m} EBITDA%"] = to_pct(mg["EBITDA%"].mean())
            rows.append(row)

        st.dataframe(
            pd.DataFrame(rows).set_index("Store"),
            use_container_width=True, height=420
        )

    st.markdown("---")

    if not fdf.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Revenue by City")
            fig = px.bar(
                fdf.groupby(["CITY", "MONTH"], observed=True)[
                    "NET_REVENUE"].sum().reset_index(),
                x="MONTH", y="NET_REVENUE", color="CITY", barmode="group",
                color_discrete_sequence=[
                    "#6c63ff", "#f0a500", "#00c9a7", "#f96060", "#45aaf2"],
                template="plotly_white"
            )
            fig.update_layout(height=320, margin=dict(l=5, r=5, t=10, b=5),
                              yaxis_title="₹", xaxis_title="",
                              plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("#### EBITDA% by Store Status")
            fig2 = px.box(
                fdf, x="STATUS", y="EBITDA%", color="STATUS",
                color_discrete_map={
                    "Active": "#00c9a7", "Inactive": "#f96060"},
                template="plotly_white", points="outliers"
            )
            fig2.update_layout(height=320, showlegend=False,
                               margin=dict(l=5, r=5, t=10, b=5),
                               plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📉 Variance by Revenue Category")
    st.caption("Variance = food wastage. Variance% = Variance ÷ Net Revenue × 100")

    st.markdown(
        '<div class="note">📌 All records have Variance% below 2%. '
        'Buckets (b), (c), (d) will show empty — this is a data characteristic, not a bug.</div>',
        unsafe_allow_html=True
    )

    sel_var = st.multiselect(
        "Select Variance Category", var_buckets
    )

    vdf = fdf[fdf["VAR_BUCKET"].isin(sel_var)] if sel_var else fdf.copy()

    st.markdown("---")
    st.markdown("#### Sub-Dashboard 1 — Avg Variance% by Revenue Category")

    if vdf.empty:
        st.warning("No data.")
    else:
        t1 = vdf.groupby(["REVENUE_COHORT", "MONTH"], observed=True)["VARIANCE%"] \
            .mean().unstack(fill_value=np.nan)
        t1 = t1.reindex([r for r in rev_cohort_order if r in t1.index])
        t1 = t1.reindex(columns=[m for m in month_list if m in t1.columns])
        t1.loc["Grand Total"] = vdf.groupby("MONTH", observed=True)["VARIANCE%"] \
            .mean().reindex(t1.columns)
        t1.index.name = "REVENUE_COHORT"

        st.dataframe(safe_format(t1), use_container_width=True)

        temp = t1.drop("Grand Total").copy()
        temp.index.name = "REVENUE_COHORT"
        plot_data = temp.reset_index().melt(
            id_vars="REVENUE_COHORT", var_name="Month", value_name="Avg Variance%"
        )
        fig3 = px.bar(
            plot_data, x="Month", y="Avg Variance%",
            color="REVENUE_COHORT", barmode="group",
            color_discrete_sequence=["#6c63ff", "#f0a500", "#00c9a7"],
            template="plotly_white"
        )
        fig3.update_layout(height=300, margin=dict(l=5, r=5, t=10, b=5),
                           legend_title="Revenue Category",
                           plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Sub-Dashboard 2 — Store Count by Revenue Range × Month")

    if vdf.empty:
        st.warning("No data.")
    else:
        t2 = vdf.groupby(["REVENUE_COHORT", "MONTH"], observed=True)["STORE"] \
            .nunique().unstack(fill_value=0)
        t2 = t2.reindex([r for r in rev_cohort_order if r in t2.index])
        t2 = t2.reindex(
            columns=[m for m in month_list if m in t2.columns], fill_value=0)
        t2.loc["Grand Total"] = vdf.groupby("MONTH", observed=True)["STORE"] \
            .nunique().reindex(t2.columns, fill_value=0)
        t2.index.name = "Revenue Category"
        st.dataframe(t2, use_container_width=True)

        fig4 = px.imshow(
            t2.drop("Grand Total").astype(float),
            text_auto=True,
            color_continuous_scale=["#eef0ff", "#6c63ff"],
            aspect="auto", template="plotly_white"
        )
        fig4.update_layout(height=240, margin=dict(l=5, r=5, t=10, b=5),
                           coloraxis_showscale=False, paper_bgcolor="white")
        st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 💡 Additional Insights")
    st.caption("Patterns found beyond the assignment spec.")

    if fdf.empty:
        st.warning("No data matches filters.")
    else:
        st.markdown("#### Best & Worst Stores by Avg EBITDA%")
        by_store = fdf.groupby(
            "STORE")["EBITDA%"].mean().sort_values(ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            fig5 = px.bar(
                by_store.head(10).reset_index(),
                x="EBITDA%", y="STORE", orientation="h",
                color="EBITDA%",
                color_continuous_scale=["#c8f7e8", "#00c9a7"],
                template="plotly_white", title="Top 10"
            )
            fig5.update_layout(height=330, yaxis=dict(autorange="reversed"),
                               coloraxis_showscale=False,
                               margin=dict(l=5, r=5, t=35, b=5),
                               plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig5, use_container_width=True)

        with c2:
            fig6 = px.bar(
                by_store.tail(10).reset_index(),
                x="EBITDA%", y="STORE", orientation="h",
                color="EBITDA%",
                color_continuous_scale=["#f96060", "#ffcccc"],
                template="plotly_white", title="Bottom 10"
            )
            fig6.update_layout(height=330, yaxis=dict(autorange="reversed"),
                               coloraxis_showscale=False,
                               margin=dict(l=5, r=5, t=35, b=5),
                               plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig6, use_container_width=True)

        st.markdown("---")
        st.markdown("#### EBITDA Negative Stores — City Trend")
        neg = fdf[fdf["EBITDA_CATEGORY"] == "EBITDA -ve"] \
            .groupby(["CITY", "MONTH"], observed=True)["STORE"].nunique().reset_index()
        neg.rename(columns={"STORE": "Count"}, inplace=True)
        fig7 = px.line(neg, x="MONTH", y="Count", color="CITY", markers=True,
                       template="plotly_white",
                       color_discrete_sequence=["#6c63ff", "#f0a500", "#00c9a7", "#f96060", "#45aaf2"])
        fig7.update_layout(height=300, margin=dict(l=5, r=5, t=10, b=5),
                           plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig7, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Active vs Inactive Store Performance")
        comp = fdf.groupby("STATUS").agg(
            Avg_Revenue=("NET_REVENUE", "mean"),
            Avg_GM=("GM%", "mean"),
            Avg_EBITDA=("EBITDA%", "mean"),
            Avg_Variance=("VARIANCE%", "mean"),
            Store_Count=("STORE", "nunique")
        ).round(2).reset_index()
        comp.columns = [
            "Status", "Avg Revenue (₹)", "Avg GM%", "Avg EBITDA%", "Avg Variance%", "Stores"]
        st.dataframe(comp, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Zone Revenue Trend")
        zone_data = fdf.groupby(["ZONE", "MONTH"], observed=True)[
            "NET_REVENUE"].sum().reset_index()
        fig8 = px.area(zone_data, x="MONTH", y="NET_REVENUE", color="ZONE",
                       template="plotly_white",
                       color_discrete_sequence=["#6c63ff", "#f0a500", "#00c9a7", "#45aaf2"])
        fig8.update_layout(height=300, margin=dict(l=5, r=5, t=10, b=5),
                           yaxis_title="₹",
                           plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig8, use_container_width=True)

        st.markdown("---")
        st.markdown("#### GM% vs EBITDA% per Store")
        st.caption(
            "Each bubble = one store. Size = total revenue. Red line = break-even.")
        scatter = fdf.groupby("STORE").agg(
            gm=("GM%", "mean"),
            eb=("EBITDA%", "mean"),
            rev=("NET_REVENUE", "sum"),
            city=("CITY", "first")
        ).reset_index()
        fig9 = px.scatter(
            scatter, x="gm", y="eb", size="rev", color="city",
            hover_name="STORE",
            hover_data={"rev": ":,.0f", "gm": ":.1f", "eb": ":.1f"},
            template="plotly_white",
            color_discrete_sequence=[
                "#6c63ff", "#f0a500", "#00c9a7", "#f96060", "#45aaf2"],
            labels={"gm": "Avg GM%", "eb": "Avg EBITDA%", "city": "City"}
        )
        fig9.add_hline(y=0, line_dash="dash", line_color="#f96060",
                       annotation_text="EBITDA = 0", annotation_font_color="#f96060")
        fig9.update_layout(height=420, margin=dict(l=5, r=5, t=10, b=5),
                           plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig9, use_container_width=True)

    st.markdown("---")
    st.caption("Kitchen P&L Dashboard · Python 3.11 · Streamlit · Pandas · Plotly")
