import os
import json
import sqlite3
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# ----------------------
# Load environment variables
# ----------------------
load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")   # OpenAI / Azure OpenAI key
AI_MODEL = "gpt-4o-mini" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # Slack Incoming Webhook URL

# ----------------------
# Slack helpers
# ----------------------
def send_slack_message(text: str):
    """Send alert/report text to Slack via incoming webhook."""
    if not SLACK_WEBHOOK_URL:
        return False
    payload = {"text": text}
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload),
                             headers={"Content-Type": "application/json"}, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print("Slack send error:", e)
        return False

# ----------------------
# Agentic AI helper
# ----------------------
def generate_ai_insights(df: pd.DataFrame) -> str:
    """
    Agentic AI analysis that explains cost drivers,
    finds optimization opportunities, and gives actions.
    """

    if df.empty:
        return "No data available for AI analysis."

    # ---- 1. Rule-based metrics from df ----
    total_cost = df["cost"].sum()
    failed_cost = df[df["conclusion"] == "failure"]["cost"].sum()

    if "is_redundant" in df.columns:
        redundant = df[df["is_redundant"]]
        redundant_cost = redundant["cost"].sum()
    else:
        redundant_cost = 0.0
        redundant = df.iloc[0:0]  # empty same-structure df

    top_branches = (
        df.groupby("branch")["cost"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
    )

    long_running = (
        df.sort_values("duration_min", ascending=False)
        .head(5)
    )

    # ---- 2. Build context string for the AI model ----
    ai_context = f"""
CI/CD Cost Summary:
Total Cost: {total_cost:.2f}
Failed Cost: {failed_cost:.2f}
Redundant Cost: {redundant_cost:.2f}

Top Expensive Branches (by cost):
{top_branches.to_string()}

Longest Running Workflows:
{long_running[['repo','branch','duration_min']].to_string(index=False)}

Your job as an AI agent:
- Identify cost anomalies and waste.
- Suggest concrete actions to reduce unnecessary spending.
- Flag redundant or stale branches and noisy workflows.
- Recommend process changes for developers.
- Estimate cost impact if failures reduce by 20%.
Respond in clear bullet points.
"""

    # ---- 3. Fallback: If no AI key, still give rule-based hints ----
    if not AI_API_KEY:
        return (
            "⚠️ AI API Key not found. Showing rule-based insights only.\n\n"
            f"Top Cost Drivers (Branches by cost):\n{top_branches}\n\n"
            "Suggestions:\n"
            "- Clean up stale branches with successful but redundant builds.\n"
            "- Reduce triggers on the most expensive branches.\n"
            "- Investigate the longest-running workflows for optimization.\n"
            "- Optimize the longest-running workflows to reduce pipeline duration."
        )

    # ---- 4. Call LLM using HTTP API ----
    try:
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": "You are an intelligent CI/CD cost optimization agent."},
                {"role": "user", "content": ai_context}
            ]
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            json=payload,
            timeout=20
        )

        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return text

    except Exception as e:
        return f"AI Error while generating insights: {e}"

# ----------------------
# SQLite helpers
# ----------------------
DB_PATH = "cicd_data.db"

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id INTEGER PRIMARY KEY,
            repo TEXT,
            name TEXT,
            status TEXT,
            conclusion TEXT,
            branch TEXT,
            created_at TEXT,
            duration_min REAL,
            cost REAL
        )
    """)
    conn.commit()
    conn.close()

def save_runs_to_db(runs_df: pd.DataFrame):
    """Insert new runs to DB (avoid duplicates)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for _, row in runs_df.iterrows():
        cursor.execute("""
            INSERT OR IGNORE INTO workflow_runs 
            (id, repo, name, status, conclusion, branch, created_at, duration_min, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["ID"], row["Repo"], row["Name"], row["Status"], row["Conclusion"],
            row["Branch"], row["Created At"].isoformat(), row["Duration (min)"], row["Cost ($)"]
        ))
    conn.commit()
    conn.close()

def fetch_runs_from_db():
    """Load all runs from SQLite as DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM workflow_runs", conn)
    conn.close()
    if not df.empty:
        df["Created At"] = pd.to_datetime(df["created_at"], utc=True)
    return df

# ----------------------
# Streamlit page config
# ----------------------
st.set_page_config(page_title="Enterprise CI/CD Monitoring Dashboard", layout="wide")
init_db()  # Ensure DB exists

# ----------------------
# Session state init
# ----------------------
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "last_alert_key" not in st.session_state:
    st.session_state["last_alert_key"] = None
if "ai_output" not in st.session_state:
    st.session_state["ai_output"] = ""


# ----------------------
# Page 1: Login
# ----------------------
if st.session_state["page"] == "login":
    st.title("🔐 GitHub / GitLab Login")
    with st.form(key="login_form_page"):
        username = st.text_input("Username / API Token Owner")
        token = st.text_input("Access Token / API Key", type="password")
        login_btn = st.form_submit_button("Login")

    if login_btn:
        if username and token:
            auth = (username, token)
            try:
                resp = requests.get("https://api.github.com/user", auth=auth, timeout=10)
            except Exception as e:
                st.error(f"Network error: {e}")
                resp = None
            if resp and resp.status_code == 200:
                st.success(f"✅ Logged in as {resp.json().get('login')}")
                st.session_state["auth"] = auth
                st.session_state["page"] = "repo"
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        else:
            st.warning("Please enter both username and token")

# ----------------------
# Page 2: Repo selection
# ----------------------
elif st.session_state["page"] == "repo":
    if st.button("⬅ Go Back to Login"):
        st.session_state["page"] = "login"
        st.rerun()

    st.title("📂 Select Repositories")
    auth = st.session_state.get("auth")
    if not auth:
        st.error("No auth found. Go back and login.")
        st.stop()

    try:
        repo_resp = requests.get("https://api.github.com/user/repos", auth=auth, timeout=15)
    except Exception as e:
        st.error(f"Failed to reach GitHub API: {e}")
        repo_resp = None

    if repo_resp and repo_resp.status_code == 200:
        repos = [r["full_name"] for r in repo_resp.json()]
        selected_repos = st.multiselect("Choose repository(s)", repos)

        st.subheader("Optional: Cloud Infrastructure APIs")
        aws_api = st.text_input("AWS API / Credentials", type="password")
        azure_api = st.text_input("Azure API / Credentials", type="password")
        gcp_api = st.text_input("GCP API / Credentials", type="password")

        st.session_state["cloud_apis"] = {"aws": aws_api, "azure": azure_api, "gcp": gcp_api}

        if st.button("Load Dashboard") and selected_repos:
            st.session_state["repo_choice"] = selected_repos
            st.session_state["page"] = "dashboard"
            st.rerun()
    else:
        st.error("❌ Failed to fetch repositories.")

# ----------------------
# Page 3: Dashboard
# ----------------------
elif st.session_state["page"] == "dashboard":
    if st.button("⬅ Go Back to Repo Selection"):
        st.session_state["page"] = "repo"
        st.rerun()

    st_autorefresh(interval=60*1000, key="refresh_dashboard")

    repos = st.session_state.get("repo_choice", [])
    auth = st.session_state.get("auth")
    if not repos or not auth:
        st.error("Missing repo selection or auth.")
        st.stop()

    st.title(f"🏢 CI/CD Monitoring Dashboard — {', '.join(repos)}")

    # Fetch new workflow runs from GitHub
    all_runs = []
    for repo_choice in repos:
        try:
            runs_resp = requests.get(f"https://api.github.com/repos/{repo_choice}/actions/runs", auth=auth, timeout=15).json()
        except Exception:
            runs_resp = {"workflow_runs": []}
        for run in runs_resp.get("workflow_runs", []):
            duration = (pd.to_datetime(run.get("updated_at")) - pd.to_datetime(run.get("created_at"))).total_seconds() / 60
            all_runs.append({
                "ID": run.get("id"),
                "Repo": repo_choice,
                "Name": run.get("name"),
                "Status": run.get("status"),
                "Conclusion": run.get("conclusion"),
                "Branch": run.get("head_branch"),
                "Created At": pd.to_datetime(run.get("created_at"), utc=True),
                "Duration (min)": duration,
                "Cost ($)": duration * 0.1
            })

    # Save to DB
    if all_runs:
        df_new = pd.DataFrame(all_runs)
        save_runs_to_db(df_new)

    # Load from DB
    df = fetch_runs_from_db()
    if df.empty:
        st.warning("No workflow data found yet.")
        st.stop()

    # ----------------------
    # Filters
    # ----------------------
    min_date = df["Created At"].dt.date.min()
    max_date = df["Created At"].dt.date.max()
    start_date, end_date = st.date_input(
        "Select start and end date", value=[min_date, max_date], min_value=min_date, max_value=max_date
    )
    df = df[(df["Created At"].dt.date >= start_date) & (df["Created At"].dt.date <= end_date)]

    branches = st.multiselect("Filter by Branch", df["branch"].unique(), default=list(df["branch"].unique()))
    df = df[df["branch"].isin(branches)]

    status_filter = st.multiselect("Filter by Status", ["success", "failure"], default=["success", "failure"])
    df = df[df["conclusion"].isin(status_filter)]

    # ----------------------
    # KPIs and cost calculation
    # ----------------------
    total_cost = df["cost"].sum()
    failed_cost = df[df["conclusion"] == "failure"]["cost"].sum()

    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=30)
    df["is_stale_branch"] = df["Created At"] < cutoff_date
    df["is_redundant"] = df["is_stale_branch"] & (df["conclusion"] == "success")
    redundant_cost = df[df["is_redundant"]]["cost"].sum()

    cloud_apis = st.session_state.get("cloud_apis", {})
    total_cost += (50 if cloud_apis.get("aws") else 0) + (30 if cloud_apis.get("azure") else 0) + (20 if cloud_apis.get("gcp") else 0)

    total_runs = len(df)
    failed_runs = int((df["conclusion"] == "failure").sum())
    success_runs = int((df["conclusion"] == "success").sum())

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Runs", total_runs)
    col2.metric("Successful Runs", success_runs)
    col3.metric("Failed Runs", failed_runs)
    col4.metric("Overall Cost ($)", round(total_cost, 2))
    col5.metric("Failed Cost ($)", round(failed_cost, 2))
    col6.metric("Redundant Cost ($)", round(redundant_cost, 2))

    # ----------------------
    # Charts
    # ----------------------

        # ----------------------
    # Agentic AI Section
    # ----------------------
    # ----------------------
# Agentic AI Section
# ----------------------
st.subheader("🤖 Agentic AI – Automated Insights & Recommendations")

# Button to (re)generate insights
if st.button("Generate AI Insights"):
    with st.spinner("AI is analysing your CI/CD workflows..."):
        st.session_state["ai_output"] = generate_ai_insights(df)

# Optional: button to clear
if st.button("Clear AI Insights"):
    st.session_state["ai_output"] = ""

# Show the latest AI output inside an open/close panel
if st.session_state["ai_output"]:
    with st.expander("📌 AI Recommendations", expanded=True):  # set False if you want it closed by default
        st.write(st.session_state["ai_output"])

    # ----------------------
    # Charts
    # ----------------------
    st.subheader("📊 Visual Insights")


    fig1 = px.bar(df, x="repo", color="conclusion", title="Success vs Failed Runs per Repo", barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(df, x="branch", y="cost", color="conclusion", title="Cost Distribution by Branch")
    st.plotly_chart(fig2, use_container_width=True)

    df["Date"] = df["Created At"].dt.date
    trend = df.groupby("Date")["cost"].sum().reset_index()
    fig3 = px.line(trend, x="Date", y="cost", title="Cost Trend Over Time")
    st.plotly_chart(fig3, use_container_width=True)

    avg_dur = df.groupby("repo")["duration_min"].mean().reset_index()
    fig4 = px.bar(avg_dur, x="repo", y="duration_min", title="Average Build Duration (min)")
    st.plotly_chart(fig4, use_container_width=True)

    # ----------------------
    # Slack report
    # ----------------------
    st.subheader("📤 Slack Reporting")

    if st.button("Send Dashboard Summary to Slack"):
        report_text = f"*CI/CD Dashboard Report* — {', '.join(repos)}\n"
        report_text += f"Total Runs: {total_runs}\nSuccessful: {success_runs}\nFailed: {failed_runs}\n"
        report_text += f"Overall Cost: ${round(total_cost,2)}\nFailed Cost: ${round(failed_cost,2)}\nRedundant Cost: ${round(redundant_cost,2)}\n"
        report_text += "\nRecent Runs:\n"
        recent = df.sort_values("Created At", ascending=False).head(5)
        for _, r in recent.iterrows():
            report_text += (
                f"{r['Created At'].strftime('%Y-%m-%d %H:%M')} | "
                f"{r['repo']} | {r['branch']} | {r['conclusion']} | "
                f"${round(r['cost'],2)}\n"
            )

        # 👉 New: add AI summary into Slack message
        ai_summary = generate_ai_insights(df)
        report_text += "\n*AI Insights:*\n"
        # avoid overly long messages in Slack
        report_text += ai_summary[:1500]

        if send_slack_message(report_text):
            st.success("✅ Report with AI insights sent to Slack")
        else:
            st.error("❌ Failed to send report to Slack")

