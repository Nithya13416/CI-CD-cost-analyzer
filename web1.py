import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# ----------------------
# Page Configuration
# ----------------------
st.set_page_config(page_title="Enterprise CI/CD Monitoring Dashboard", layout="wide")

# Initialize navigation state
if "page" not in st.session_state:
    st.session_state["page"] = "login"   # default first page

# ----------------------
# Page 1: Login
# ----------------------
# ----------------------
# Page 1: Login
# ----------------------
if st.session_state["page"] == "login":
    st.title("🔐 GitHub / GitLab Login")
    with st.form(key="login_form_page"):
        username = st.text_input("Username / API Token Owner")
        token = st.text_input("Access Token / API Key", type="password")  # Masked
        login_btn = st.form_submit_button("Login")

    if login_btn:
        if username and token:
            auth = (username, token)
            # Example: Try GitHub API
            resp = requests.get("https://api.github.com/user", auth=auth)
            if resp.status_code == 200:
                st.success(f"✅ Logged in as {resp.json()['login']}")
                st.session_state["auth"] = auth  # stored safely in session
                st.session_state["page"] = "repo"
                st.rerun()
            else:
                st.error("❌ Invalid credentials or token")
        else:
            st.warning("Please enter both username and token")

# ----------------------
# Page 2: Repository Selection
# ----------------------
elif st.session_state["page"] == "repo":
    if st.button("⬅ Go Back to Login"):
        st.session_state["page"] = "login"
        st.rerun()

    st.title("📂 Select Repositories")
    auth = st.session_state["auth"]

    repo_resp = requests.get("https://api.github.com/user/repos", auth=auth)
    if repo_resp.status_code == 200:
        repos = [r["full_name"] for r in repo_resp.json()]
        selected_repos = st.multiselect("Choose repository(s)", repos)

        # Optional Cloud API input (all masked)
        st.subheader("Optional: Cloud Infrastructure APIs")
        aws_api = st.text_input("AWS Billing API / Credentials", type="password")
        azure_api = st.text_input("Azure Billing API / Credentials", type="password")
        gcp_api = st.text_input("GCP Billing API / Credentials", type="password")

        # Store securely in session_state
        st.session_state["cloud_apis"] = {
            "aws": aws_api,
            "azure": azure_api,
            "gcp": gcp_api
        }

        if st.button("Load Dashboard") and selected_repos:
            st.session_state["repo_choice"] = selected_repos
            st.session_state["page"] = "dashboard"
            st.rerun()
    else:
        st.error("❌ Failed to fetch repositories. Check permissions.")

# ----------------------
# Page 3: Dashboard
# ----------------------
elif st.session_state["page"] == "dashboard":
    if st.button("⬅ Go Back to Repo Selection"):
        st.session_state["page"] = "repo"
        st.rerun()

    st_autorefresh(interval=60 * 1000, key="refresh_dashboard")

    repos = st.session_state["repo_choice"]
    auth = st.session_state["auth"]

    st.title(f"🏢 CI/CD Monitoring Dashboard — {', '.join(repos)}")

    all_runs = []
    for repo_choice in repos:
        runs_resp = requests.get(f"https://api.github.com/repos/{repo_choice}/actions/runs", auth=auth).json()
        workflow_runs = runs_resp.get("workflow_runs", [])
        for run in workflow_runs:
            all_runs.append({
                "Repo": repo_choice,
                "ID": run["id"],
                "Name": run["name"],
                "Status": run["status"],
                "Conclusion": run["conclusion"],
                "Branch": run["head_branch"],
                "Created At": pd.to_datetime(run["created_at"], utc=True),
                "Duration (min)": (pd.to_datetime(run["updated_at"]) - pd.to_datetime(run["created_at"])).total_seconds() / 60
            })

    if not all_runs:
        st.warning("No workflow runs found for the selected repositories.")
        st.stop()

    df = pd.DataFrame(all_runs)

    # ----------------------
    # Filters
    # ----------------------
    st.subheader("📌 Filters")
    # Date range filter
    min_date = df["Created At"].dt.date.min()
    max_date = df["Created At"].dt.date.max()
    start_date, end_date = st.date_input(
        "Select start and end date",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    df = df[(df["Created At"].dt.date >= start_date) & (df["Created At"].dt.date <= end_date)]

    # Branch filter
    branches = st.multiselect("Filter by Branch", df["Branch"].unique(), default=list(df["Branch"].unique()))
    df = df[df["Branch"].isin(branches)]

    # Status filter
    status_filter = st.multiselect("Filter by Status", ["success", "failure"], default=["success", "failure"])
    df = df[df["Conclusion"].isin(status_filter)]

    # ----------------------
    # KPIs (row of 6 metrics)
    # ----------------------
    df["Cost ($)"] = df["Duration (min)"] * 0.1
    total_cost = df["Cost ($)"].sum()
    failed_cost = df[df["Conclusion"] == "failure"]["Cost ($)"].sum()

    # Redundant cost calculation
    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=30)
    df["is_stale_branch"] = df["Created At"] < cutoff_date
    df["is_redundant"] = df["is_stale_branch"] & (df["Conclusion"] == "success")
    redundant_cost = df[df["is_redundant"]]["Cost ($)"].sum()

    # Cloud cost calculation
    def fetch_aws_cost(api): return 50 if api else 0
    def fetch_azure_cost(api): return 30 if api else 0
    def fetch_gcp_cost(api): return 20 if api else 0

    cloud_apis = st.session_state.get("cloud_apis", {})
    cloud_cost = (
        fetch_aws_cost(cloud_apis.get("aws")) +
        fetch_azure_cost(cloud_apis.get("azure")) +
        fetch_gcp_cost(cloud_apis.get("gcp"))
    )
    total_cost += cloud_cost

    # KPI metrics
    total_runs = len(df)
    failed_runs = (df["Conclusion"] == "failure").sum()
    success_runs = (df["Conclusion"] == "success").sum()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Runs", total_runs)
    col2.metric("Successful Runs", success_runs)
    col3.metric("Failed Runs", failed_runs)
    col4.metric("Overall Cost ($)", round(total_cost, 2))
    col5.metric("Failed Cost ($)", round(failed_cost, 2))
    col6.metric("Redundant Cost ($)", round(redundant_cost, 2))

    # ----------------------
    # Tabs for better layout
    # ----------------------
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "💰 Costs", "📊 Distributions", "📋 Details"])

    # Trends
    with tab1:
        colA, colB = st.columns(2)
        df_trend = df.groupby(df["Created At"].dt.date).size().reset_index(name="Run Count")
        fig_trend = px.line(df_trend, x="Created At", y="Run Count", markers=True, title="Workflow Runs Trend")
        colA.plotly_chart(fig_trend, use_container_width=True)

        df_success_fail = df.groupby([df["Created At"].dt.date, "Conclusion"]).size().reset_index(name="Count")
        fig_sf = px.bar(df_success_fail, x="Created At", y="Count", color="Conclusion", title="Success vs Failures")
        colB.plotly_chart(fig_sf, use_container_width=True)

    # Costs
    with tab2:
        df_cost_trend = df.groupby(df["Created At"].dt.date)["Cost ($)"].sum().reset_index()
        fig_cost = px.line(df_cost_trend, x="Created At", y="Cost ($)", markers=True, title="Workflow Cost Trend")
        st.plotly_chart(fig_cost, use_container_width=True)

    # Distributions
    with tab3:
        colC, colD = st.columns(2)
        conclusion_counts = df['Conclusion'].value_counts().reset_index()
        conclusion_counts.columns = ['Conclusion', 'Count']
        fig_pie = px.pie(conclusion_counts, names='Conclusion', values='Count', title='Workflow Outcomes')
        colC.plotly_chart(fig_pie, use_container_width=True)

        branch_counts = df['Branch'].value_counts().reset_index()
        branch_counts.columns = ['Branch', 'Count']
        fig_bar = px.bar(branch_counts, x='Branch', y='Count', title='Runs by Branch')
        colD.plotly_chart(fig_bar, use_container_width=True)

    # Details
    with tab4:
        def highlight_failures(row):
            color = ""
            if row['Conclusion'] == 'failure':
                color = 'background-color: #ffcccc'
            elif row['Conclusion'] == 'success':
                color = 'background-color: #ccffcc'
            return [color]*len(row)

        st.dataframe(df.style.apply(highlight_failures, axis=1))


