import os
import streamlit as st
import pandas as pd
import duckdb
from dotenv import load_dotenv
import requests
import plotly.express as px
from functools import lru_cache

# ---------------------------
# Page / theme / CSS
# ---------------------------
st.set_page_config(
    page_title="MAER.AI — Conversational Commerce Analyst",
    layout="wide",
    initial_sidebar_state="expanded"  # ✅ keep sidebar visible
)

def inject_custom_css():
    st.markdown("""
        <style>
        /* =========================
           APPLE x IBM VISION UI
           (no logic changes)
           ========================= */
        :root{
          --bg-dark:#080A10;
          --panel:rgba(255,255,255,0.05);
          --accent1:#0F62FE;   /* IBM blue */
          --accent2:#00C6FF;   /* Apple aqua */
          --accent3:#C7E5FF;   /* soft silver */
          --text:#E9EEF6;
          --line:rgba(255,255,255,0.12);
          --shadow:0 8px 40px rgba(0,0,0,0.35);
        }

        /* Fonts */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');
        html, body, [class*="css"] {
          font-family:'IBM Plex Sans','SF Pro Display',-apple-system,BlinkMacSystemFont,sans-serif !important;
          scroll-behavior:smooth;
        }

        /* Background glow */
        .main {
          background:
            radial-gradient(900px 600px at 45% -20%, rgba(15,98,254,0.16), transparent 60%),
            radial-gradient(1100px 750px at 82% 110%, rgba(0,198,255,0.12), transparent 60%),
            linear-gradient(180deg,#07090F,#0B0E14) !important;
          animation:bgShift 16s ease-in-out infinite alternate;
        }
        @keyframes bgShift {
          0%{background-position:0 0,50% 50%;}
          100%{background-position:30px 60px,40% 45%;}
        }

        /* Sidebar glass */
        [data-testid="stSidebar"]{
          background:rgba(12,14,20,0.72)!important;
          backdrop-filter:blur(18px);
          border-right:1px solid var(--line);
          box-shadow:inset 0 0 40px rgba(255,255,255,0.03);
        }

        /* Sidebar logo */
        .maer-logo{
          display:flex;align-items:center;gap:12px;
          padding:12px 10px 22px 10px;
          border-bottom:1px solid var(--line);
        }
        .maer-logo .brand{
          font-weight:700;letter-spacing:.6px;
          font-size:18px;
          background:linear-gradient(90deg,var(--accent2),var(--accent1),#B8E5FF);
          -webkit-background-clip:text;color:transparent;
        }

        /* Header */
        .brand-header{
          display:flex;align-items:center;gap:16px;margin-top:-10px;margin-bottom:6px;
        }
        .brand-title{
          font-size:clamp(30px,3.4vw,48px);
          font-weight:700;letter-spacing:.2px;
          background:linear-gradient(90deg,#FFFFFF,#CFEAFF,#00C6FF);
          -webkit-background-clip:text;color:transparent;
          text-shadow:0 0 22px rgba(0,198,255,0.18);
        }
        .brand-chip{
          background:rgba(255,255,255,0.07);
          border-radius:999px;color:#D6E0EA;font-size:12px;
          padding:6px 12px;border:1px solid rgba(255,255,255,0.15);
          backdrop-filter:blur(12px);
        }
        .accent-line{
          height:2px;margin-top:8px;border-radius:2px;opacity:.6;
          background:linear-gradient(90deg,#00C6FF,#0F62FE,#FFFFFF);
        }

        /* Metrics */
        div[data-testid="metric-container"]{
          background:var(--panel);
          border:1px solid var(--line);
          border-radius:16px;
          box-shadow:var(--shadow);
          backdrop-filter:blur(24px);
          transition:transform .25s ease,box-shadow .25s ease;
        }
        div[data-testid="metric-container"]:hover{
          transform:translateY(-2px);
          box-shadow:0 8px 40px rgba(0,198,255,0.25);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
        .stTabs [data-baseweb="tab"]{
          background:rgba(255,255,255,0.03);
          border:1px solid rgba(255,255,255,0.07);
          border-radius:12px 12px 0 0;
          color:#EAF2FF;padding:10px 16px;transition:all .2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover{
          transform:translateY(-1px);
          box-shadow:0 6px 18px rgba(0,198,255,0.18);
        }
        .stTabs [aria-selected="true"]{
          background:linear-gradient(90deg,rgba(0,198,255,0.2),rgba(15,98,254,0.24));
          color:white;border-bottom:2px solid #00C6FF;
        }

        /* Buttons */
        button[kind="primary"]{
          background:linear-gradient(90deg,#00C6FF,#0F62FE)!important;
          border-radius:10px!important;border:0!important;color:#fff!important;
          box-shadow:0 6px 18px rgba(0,198,255,0.25);
          transition:all .25s ease;
        }
        button[kind="primary"]:hover{transform:translateY(-1px) scale(1.02);}

        .stDownloadButton button{
          background:linear-gradient(90deg,#A8EFFF,#00C6FF)!important;
          border-radius:10px;color:#000!important;transition:all .25s ease;
        }
        .stDownloadButton button:hover{transform:translateY(-1px);}

        /* Chat */
        .stChatMessage{
          background:rgba(255,255,255,0.03);
          border:1px solid rgba(255,255,255,0.07);
          border-radius:14px;padding:14px;backdrop-filter:blur(15px);
        }
        .stChatMessage [data-testid="stMarkdownContainer"] p{color:var(--text);}
        pre,code{color:#CFEAFF!important;background:rgba(255,255,255,0.04)!important;border-radius:10px;}

        /* Hide default chrome: keep header visible for sidebar toggle */
        #MainMenu, footer {visibility:hidden;}  /* ✅ header no longer hidden */
        </style>
    """, unsafe_allow_html=True)

def render_brand_header():
    # Hex-chip AI logo (header)
    st.markdown("""
        <div class="brand-header">
          <svg width="50" height="50" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="hx" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#00C6FF"/>
                <stop offset="100%" stop-color="#0F62FE"/>
              </linearGradient>
              <radialGradient id="core" cx="50%" cy="50%" r="60%">
                <stop offset="0%" stop-color="#EFFFFF"/>
                <stop offset="60%" stop-color="#BFE8FF"/>
                <stop offset="100%" stop-color="#00C6FF"/>
              </radialGradient>
            </defs>
            <!-- Hex frame -->
            <polygon points="60,10 102,34 102,86 60,110 18,86 18,34"
                     fill="none" stroke="url(#hx)" stroke-width="3"/>
            <!-- Chips / neurons -->
            <circle cx="60" cy="60" r="18" fill="url(#core)"/>
            <circle cx="35" cy="50" r="4" fill="url(#hx)"/>
            <circle cx="85" cy="50" r="4" fill="url(#hx)"/>
            <circle cx="45" cy="85" r="3" fill="url(#hx)"/>
            <circle cx="75" cy="85" r="3" fill="url(#hx)"/>
            <line x1="35" y1="50" x2="60" y2="60" stroke="url(#hx)" stroke-width="2" />
            <line x1="85" y1="50" x2="60" y2="60" stroke="url(#hx)" stroke-width="2" />
            <line x1="45" y1="85" x2="60" y2="60" stroke="url(#hx)" stroke-width="1.8" />
            <line x1="75" y1="85" x2="60" y2="60" stroke="url(#hx)" stroke-width="1.8" />
          </svg>
          <div class="brand-title">MAER.AI — Conversational Commerce Analyst</div>
          <div class="brand-chip">Gemini + DuckDB • Live SQL • Executive Insights</div>
        </div>
        <div class="accent-line"></div>
    """, unsafe_allow_html=True)

def render_sidebar_logo():
    # Compact hex-chip logo (sidebar)
    st.sidebar.markdown("""
        <div class="maer-logo">
          <svg width="30" height="30" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="hxs" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#00C6FF"/>
                <stop offset="100%" stop-color="#0F62FE"/>
              </linearGradient>
            </defs>
            <polygon points="60,12 100,35 100,85 60,108 20,85 20,35"
                     fill="none" stroke="url(#hxs)" stroke-width="5"/>
            <circle cx="60" cy="60" r="10" fill="url(#hxs)"/>
          </svg>
          <div class="brand">MAER.AI</div>
        </div>
    """, unsafe_allow_html=True)

inject_custom_css()
render_sidebar_logo()

# ---------------------------
# Secrets (Streamlit Cloud)
# ---------------------------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_NAME = st.secrets.get("MODEL_NAME", "gemini-2.0-flash")


# ---------------------------
# Title & Tabs
# ---------------------------
st.title(" ")
render_brand_header()
st.caption("Conversational analytics powered by Gemini + DuckDB")
tab_chat, tab_dashboard, tab_lab = st.tabs(["💬 Chat", "📊 Dashboard", "🧪 SQL Lab"])

# ---------------------------
# Memory / Schema / Guardrails
# ---------------------------
def get_chat_memory():
    if "chat_memory" not in st.session_state:
        st.session_state["chat_memory"] = []
    return st.session_state["chat_memory"]

def append_memory(role: str, content: str):
    mem = get_chat_memory()
    mem.append({"role": role, "content": content})
    if len(mem) > 15:
        mem.pop(0)

def summarize_memory() -> str:
    mem = get_chat_memory()
    return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in mem[-6:]])

@lru_cache(maxsize=1)
def get_schema(conn):
    tables = conn.execute("SHOW TABLES").fetchdf()["name"].tolist()
    out = []
    for t in tables:
        cols = conn.execute(f"PRAGMA table_info({t})").fetchdf()
        out.append(f"- {t}({', '.join(cols['name'].tolist()[:10])})")
    return "\n".join(out)

def normalize_sql(sql: str) -> str:
    """
    Cleans Gemini output by:
    - removing reasoning lines (# ...)
    - removing markdown code fences
    - preserving all valid SQL clauses
    - fixing incomplete SQL by falling back safely
    """
    if not sql:
        return "SELECT 'Error: Empty SQL from model' AS message;"

    # Remove markdown wrappers and stray characters
    cleaned = (
        sql.replace("```sql", "")
           .replace("```", "")
           .replace("`", "")
           .strip()
    )

    # List of allowed SQL beginnings
    valid_starts = (
        "select", "with", "from", "where", "group by",
        "order by", "having", "join", "left join",
        "right join", "inner join", "limit"
    )

    extracted_lines = []
    for line in cleaned.splitlines():
        stripped = line.strip().lower()

        # Skip reasoning or explanation lines
        if stripped.startswith("#"):
            continue

        # Keep any line starting with a valid SQL keyword
        if any(stripped.startswith(start) for start in valid_starts):
            extracted_lines.append(line)
            continue

    # If nothing was captured, fallback to safe default
    if not extracted_lines:
        return "SELECT * FROM sales_enriched LIMIT 20;"

    # Reconstruct SQL
    final_sql = "\n".join(extracted_lines).strip()

    # Ensure the query ends with a semicolon
    if not final_sql.endswith(";"):
        final_sql += ";"

    return final_sql



# ---------------------------
# Data loading
# ---------------------------
def load_data_into_duckdb(data_path="data/olist"):
    conn = duckdb.connect(database=":memory:")
    for f in os.listdir(data_path):
        if f.endswith(".csv"):
            name = os.path.splitext(f)[0]
            conn.execute(
                f"CREATE OR REPLACE VIEW {name} AS "
                f"SELECT * FROM read_csv_auto('{os.path.join(data_path,f)}', HEADER=TRUE)"
            )
    conn.execute("""
        CREATE OR REPLACE VIEW sales_enriched AS
        SELECT oi.order_id,oi.product_id,p.product_category_name AS category,
               CAST(oi.price AS DOUBLE) AS price,CAST(oi.freight_value AS DOUBLE) AS freight_value,
               o.order_status,o.order_purchase_timestamp,o.order_delivered_customer_date,
               c.customer_city,c.customer_state,pay.payment_type,
               CAST(pay.payment_value AS DOUBLE) AS payment_value,
               CAST(r.review_score AS DOUBLE) AS review_score
        FROM olist_order_items_dataset oi
        JOIN olist_orders_dataset o ON oi.order_id=o.order_id
        LEFT JOIN olist_products_dataset p ON oi.product_id=p.product_id
        LEFT JOIN olist_customers_dataset c ON o.customer_id=c.customer_id
        LEFT JOIN olist_order_payments_dataset pay ON o.order_id=pay.order_id
        LEFT JOIN olist_order_reviews_dataset r ON o.order_id=r.order_id;
    """)
    return conn

# ---------------------------
# KPI helpers
# ---------------------------
def kpi_df(conn):
    return conn.execute("""
        SELECT COUNT(DISTINCT order_id) AS total_orders,
               SUM(payment_value) AS total_revenue,
               COUNT(DISTINCT customer_city) AS unique_customers,
               AVG(review_score) AS avg_rating
        FROM sales_enriched
    """).fetchdf()

def monthly_revenue_df(conn):
    return conn.execute("""
        SELECT strftime(order_purchase_timestamp,'%Y-%m') AS month,
               SUM(price) AS revenue
        FROM sales_enriched GROUP BY month ORDER BY month
    """).fetchdf()

def top_categories_df(conn,limit=10):
    return conn.execute(f"""
        SELECT COALESCE(category,'unknown') AS category,SUM(price) AS total_sales
        FROM sales_enriched GROUP BY category ORDER BY total_sales DESC LIMIT {int(limit)}
    """).fetchdf()

# ---------------------------
# Gemini call
# ---------------------------
def ask_gemini(prompt:str)->str:
    if not GEMINI_API_KEY:
        return "Error: Missing GEMINI_API_KEY"
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    res=requests.post(url,json={"contents":[{"parts":[{"text":prompt}]}]},timeout=60)
    try:
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "Error: "+str(res.text)[:400]

# ---------------------------
# Sidebar setup / controls
# ---------------------------
with st.sidebar:
    st.header("⚙️ Setup")
    data_path = st.text_input("Dataset folder", value="data/olist")
    if st.button("Load Dataset", type="primary"):
        with st.spinner("Loading dataset…"):
            st.session_state["conn"]=load_data_into_duckdb(data_path)
        st.success("✅ Dataset loaded successfully!")

    st.markdown("---")
    st.subheader("🧠 Agent Controls")
    if st.button("🧹 Reset Memory"):
        st.session_state["chat_memory"] = []
        st.success("Conversation memory cleared!")
    show_reason = st.toggle("🤖 Show Agent Reasoning", value=False, key="show_reasoning")

    st.markdown("---")
    st.subheader("🎬 Demo queries")
    demo = st.radio("Pick one:",[
        "Top 5 categories by total sales",
        "Monthly revenue trend",
        "Best states by average review score",
        "Payment methods share"],index=None)
    if demo and "conn" in st.session_state:
        qmap={
            "Top 5 categories by total sales":"SELECT category,SUM(price) AS total_sales FROM sales_enriched GROUP BY category ORDER BY total_sales DESC LIMIT 5",
            "Monthly revenue trend":"SELECT strftime(order_purchase_timestamp,'%Y-%m') AS month,SUM(price) AS revenue FROM sales_enriched GROUP BY month ORDER BY month",
            "Best states by average review score":"SELECT customer_state,AVG(review_score) AS avg_score FROM sales_enriched GROUP BY customer_state HAVING COUNT(*)>50 ORDER BY avg_score DESC LIMIT 10",
            "Payment methods share":"SELECT payment_type,SUM(payment_value) AS total_value FROM sales_enriched GROUP BY payment_type ORDER BY total_value DESC"
        }
        st.session_state["preset_query"]=qmap[demo]

# If dataset not loaded yet
if "conn" not in st.session_state:
    st.info("⬅️ Load the dataset from the sidebar to begin.")   # ← Arrow to left sidebar
    st.stop()
conn=st.session_state["conn"]

# ---------------------------
# Dashboard (safe + verified)
# ---------------------------
with tab_dashboard:
    try:
        # Check if the key view exists before running any SQL
        views = conn.execute("SHOW TABLES").fetchdf()["name"].tolist()
        if "sales_enriched" not in views:
            st.warning("⚠️ 'sales_enriched' view not found in DuckDB. Please reload your dataset.")
            st.stop()

        kpis = kpi_df(conn)

        if not kpis.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Total Revenue", f"${kpis['total_revenue'].iloc[0]:,.2f}")
            c2.metric("📦 Total Orders", f"{int(kpis['total_orders'].iloc[0]):,}")
            c3.metric("🏙️ Unique Cities", f"{int(kpis['unique_customers'].iloc[0]):,}")
            c4.metric("⭐ Avg Review", f"{kpis['avg_rating'].iloc[0]:.2f}")
        else:
            st.warning("⚠️ KPI data returned empty — please verify the CSVs inside your dataset folder.")

        # Divider and plots
        st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)
        st.markdown("### 📊 Visual Insights")

        left, right = st.columns([1.1, 1])
        with left:
            cat_df = top_categories_df(conn)
            if not cat_df.empty:
                fig = px.bar(cat_df, x="category", y="total_sales", title="Top 10 Categories by Sales")
                fig.update_traces(hovertemplate="<b>%{x}</b><br>Total: %{y:,.0f}<extra></extra>")
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color="#DCE8F7",
                    xaxis_title=None, yaxis_title="Total Sales",
                    margin=dict(l=10, r=10, t=60, b=10),
                    transition_duration=500
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("ℹ️ No category data available yet.")
        with right:
            rev_df = monthly_revenue_df(conn)
            if not rev_df.empty:
                fig2 = px.line(rev_df, x="month", y="revenue", markers=True, title="Monthly Revenue Trend")
                fig2.update_traces(hovertemplate="<b>%{x}</b><br>Revenue: %{y:,.0f}<extra></extra>")
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color="#DCE8F7",
                    xaxis_title=None, yaxis_title="Revenue",
                    margin=dict(l=10, r=10, t=60, b=10),
                    transition_duration=600
                )
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("ℹ️ No monthly revenue trend data available yet.")

        # ✨ Your brand signature (consistent across MAER.AI)
        st.markdown("""
            <div style="
                text-align:center;
                margin-top:15px;
                font-size:14px;
                font-weight:600;
                letter-spacing:0.3px;
                background:linear-gradient(90deg,#00C6FF,#0F62FE,#C7E5FF);
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
                text-shadow:0 0 10px rgba(0,198,255,0.3);
            ">
            MAER.AI • Dashboard • © Anvitha Anand
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"🚨 Dashboard Error: {e}")



# ---------------------------
# CHAT TAB (with reasoning + safe fallback for tabulate)
# ---------------------------
with tab_chat:
    st.markdown("### 💬 Ask MAER.AI")
    user_query = st.chat_input("Ask something about the Olist dataset…")
    preset_query = st.session_state.get("preset_query")

    if preset_query:
        st.chat_message("assistant").markdown("**SQL Generated (preset):**")
        st.code(preset_query, language="sql")
        try:
            df = conn.execute(preset_query).fetchdf()
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")
        st.session_state["preset_query"] = None

    if user_query:
        append_memory("user", user_query)
        st.chat_message("user").markdown(user_query)

        # ---------------------------
        # UPDATED PROMPT (date-safe)
        # ---------------------------
        with st.spinner("Reasoning and generating SQL with Gemini…"):
            schema_text = get_schema(conn)
            reasoning_context = summarize_memory()

            prompt = f"""
You are MAER.AI, a senior data analyst for an ecommerce platform using DuckDB.

IMPORTANT DATE RULES (strict):
- The Olist dataset contains historical timestamps (2016–2018).
- NEVER use CURRENT_DATE, NOW(), TODAY(), or system time.
- ALL date comparisons MUST be relative to:
    (SELECT MAX(order_purchase_timestamp) FROM sales_enriched)

Examples you MUST follow:
- "last month" →
    DATE_TRUNC('month', order_purchase_timestamp)
    = DATE_TRUNC('month', (SELECT MAX(order_purchase_timestamp) FROM sales_enriched) - INTERVAL 1 MONTH)

- "this month" →
    DATE_TRUNC('month', order_purchase_timestamp)
    = DATE_TRUNC('month', (SELECT MAX(order_purchase_timestamp) FROM sales_enriched))

- "last 3 months" →
    order_purchase_timestamp >= 
    (SELECT MAX(order_purchase_timestamp) FROM sales_enriched) - INTERVAL 3 MONTH

- "last week" →
    order_purchase_timestamp >=
    (SELECT MAX(order_purchase_timestamp) FROM sales_enriched) - INTERVAL 7 DAY

- NEVER assume today's real date.

Now, as usual:
First, provide reasoning in 3–5 lines prefixed with '#'.
Then output ONLY the final valid DuckDB SQL query.

Schema:
{schema_text}

Conversation memory:
{reasoning_context}

User question:
{user_query}
"""

            sql_text = ask_gemini(prompt)

        cleaned = normalize_sql(sql_text)
        reasoning_lines = [l for l in sql_text.splitlines() if l.strip().startswith('#')]

        # --- Show reasoning trace if toggle enabled ---
        if show_reason and reasoning_lines:
            st.markdown("#### 🧩 Agent Reasoning Trace")
            st.code("\n".join(reasoning_lines), language="text")

        # --- Show SQL ---
        st.chat_message("assistant").markdown("**SQL Generated:**")
        st.code(cleaned, language="sql")

        try:
            df = conn.execute(cleaned).fetchdf()
        except Exception as e:
            error_msg = str(e)
            st.warning(f"⚠️ SQL Error: {error_msg}")
            st.info("🔄 Retrying with SQL correction…")

            fix_prompt = f"""
Fix this SQL for DuckDB.

Schema:
{schema_text}

Original SQL:
{cleaned}

Error:
{error_msg}

Return ONLY valid SQL.
"""
            fixed_sql = normalize_sql(ask_gemini(fix_prompt))
            st.code(fixed_sql, language="sql")
            df = conn.execute(fixed_sql).fetchdf()
            append_memory("assistant", f"Fixed SQL: {fixed_sql}")

        append_memory("assistant", f"SQL: {cleaned}")

        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "⬇️ Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="maer_ai_results.csv",
                mime="text/csv"
            )

            try:
                try:
                    preview = df.head(10).to_markdown(index=False)
                except Exception:
                    preview = df.head(10).to_string(index=False)

                insight_prompt = f"""
You are a senior business analyst.
Summarize this table into 2–3 actionable insights considering previous chat memory:
{summarize_memory()}

Table:
{preview}
"""

                insight = ask_gemini(insight_prompt)
                if insight and not insight.startswith("Error"):
                    st.markdown(f"🧠 **Executive Insight**\n\n{insight}")
                    append_memory("assistant", f"Insight: {insight}")

            except Exception as e:
                st.warning(f"Insight generation skipped ({e})")
        else:
            st.warning("No results returned.")

    st.caption("MAER.AI • Chat • © Anvitha Anand")


# ---------------------------
# SQL LAB TAB (safe + branded)
# ---------------------------
with tab_lab:
    st.markdown("### 🧪 SQL Lab")
    st.info("Write, run, and test custom DuckDB SQL queries on your loaded dataset.", icon="🧠")

    # Check for active dataset connection
    try:
        views = conn.execute("SHOW TABLES").fetchdf()["name"].tolist()
        if not views:
            st.warning("⚠️ No tables found. Please load a dataset from the sidebar first.")
            st.stop()
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}")
        st.stop()

    # SQL input area
    sql_manual = st.text_area(
        "Enter your DuckDB SQL below 👇",
        value=(
            "SELECT category, SUM(price) AS total_sales "
            "FROM sales_enriched "
            "GROUP BY category "
            "ORDER BY total_sales DESC LIMIT 20;"
        ),
        height=140,
    )

    # Action buttons
    run_col, clear_col = st.columns([0.25, 0.25])
    with run_col:
        if st.button("▶️ Run SQL", use_container_width=True):
            try:
                df = conn.execute(sql_manual).fetchdf()
                if df.empty:
                    st.warning("No rows returned — try a different query.")
                else:
                    st.success(f"✅ Query executed successfully — {len(df)} rows fetched.")
                    st.dataframe(df, use_container_width=True)

                    # Optional download
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=df.to_csv(index=False).encode("utf-8"),
                        file_name="sql_lab_results.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            except Exception as e:
                st.error(f"❌ SQL Execution Error:\n\n{e}")

    with clear_col:
        if st.button("🧹 Clear", use_container_width=True):
            st.rerun()

    # Brand signature
    st.markdown(
        "<hr style='border:0.5px solid rgba(255,255,255,0.12)'>"
        "<div style='text-align:center; opacity:0.75; font-size:13px; color:#CFE0F5'>"
        "🧪 MAER.AI • SQL Lab • © Anvitha Anand"
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------
# Footer Branding
# ---------------------------
st.markdown("""
<hr style="border:0.5px solid rgba(255,255,255,0.12)">
<div style="text-align:center; opacity:0.75; font-size:13px; color:#CFE0F5">
🤖 Built by <b>Anvitha Anand</b> • Powered by Gemini + DuckDB + Streamlit
</div>
""", unsafe_allow_html=True)
