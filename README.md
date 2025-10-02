Problem Statement

In modern software development, organizations often rely on CI/CD pipelines (GitHub Actions, GitLab CI, etc.) to automate building, testing, and deploying code. While CI/CD improves efficiency, it also introduces challenges:

Lack of centralized monitoring – Teams managing multiple repositories cannot easily track workflow runs, failures, or resource usage across repos.

Cost tracking difficulty – CI/CD workflows consume compute resources, and organizations often pay for unused or redundant runs. Cloud infrastructure costs (AWS, Azure, GCP) add to the complexity.

Time inefficiency – Developers spend time manually checking pipeline statuses or generating reports.

Data fragmentation – Insights are scattered across GitHub/GitLab dashboards and cloud billing tools, making it hard to analyze trends, failures, and cost optimization opportunities.

Goal: Build a single, user-friendly dashboard that consolidates CI/CD run metrics, highlights failures, calculates costs, and allows filtering by repository, branch, and workflow status.

Objectives

The main objectives of this project are:

Centralized CI/CD Monitoring

Fetch workflow runs from multiple GitHub or GitLab repositories.

Display workflow run details such as status, conclusion, branch, and duration.

Cost Analysis

Calculate total, failed, and redundant CI/CD run costs based on workflow duration.

Include optional cloud infrastructure costs from AWS, Azure, and GCP.

Real-Time Dashboard

Provide auto-refreshing metrics to track pipeline performance in real time.

Visualize trends, distributions, and detailed workflow information using charts and tables.

Custom Filtering & KPIs

Allow users to filter data by date range, branch, or workflow status.

Show key metrics like total runs, successful runs, failed runs, and cost breakdowns.

Security & Privacy

Ensure sensitive credentials (API tokens, cloud keys) are masked and not stored in the code or logs.

User-Friendly Interface

Use Streamlit for a simple, interactive, web-based interface.

Include navigation between Login, Repository Selection, and Dashboard pages.

Solution

The solution is a Streamlit-based web dashboard that integrates with GitHub/GitLab APIs and optionally with cloud billing APIs to provide centralized monitoring, cost tracking, and analytics:

Login Page

Users enter GitHub/GitLab username and personal access token securely.

Token is masked in the UI and stored only in session state.

Repository Selection

Users can select one or multiple repositories to monitor.

Optional input for cloud API credentials to factor in infrastructure costs.

Dashboard Page

Displays KPIs: total runs, successful/failed runs, overall/failed/redundant costs.

Provides interactive filters for date range, branch, and workflow status.

Visualizations include trend lines, bar charts, pie charts, and detailed tables.

Auto-refreshes every minute to show up-to-date pipeline data.

Cost Calculation Logic

Workflow duration × cost-per-minute gives CI/CD run cost.

Redundant runs are detected (e.g., success runs on stale branches).

Cloud costs are optionally included.

Security Measures

All sensitive inputs are masked (type="password").

.env files or other secret storage files are ignored in Git.

API tokens are never printed or exposed in logs or DataFrames.

Benefits

Centralized monitoring reduces manual tracking effort.

Cost visualization enables better resource optimization.

Clear insights into failures and redundant runs help improve CI/CD efficiency.
