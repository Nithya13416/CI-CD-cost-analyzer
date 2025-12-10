# CI/CD Cost Analyzer

AI-Powered Monitoring • Workflow Insights • Cost Optimization

This repository contains an enterprise-focused CI/CD Cost Intelligence Platform designed to help engineering and DevOps teams monitor pipeline performance, analyze workflow cost drivers, and automate optimization using Agentic AI.

The solution integrates GitHub Actions data, cost modeling, Slack notifications, and real-time analytics inside a modern Streamlit dashboard.
---

##HLD
<img width="1223" height="444" alt="image" src="https://github.com/user-attachments/assets/13cf1450-d52f-42dc-b354-c95a3e0f5aab" />

✨ Key Capabilities
1. Unified CI/CD Monitoring Dashboard
  *Authenticate using GitHub username + token
  *Select one or more repositories to monitor
  *Auto-refreshing pipeline metrics
  *Historical data retention using SQLite

2. Cost Modeling & Efficiency Metrics
  *The system computes:
  *Total pipeline cost
  *Failed workflow cost
  *Redundant/stale branch cost
  *Duration-based cost modeling
  *Cost-per-branch, cost-per-repository
  *Failure vs Success impact on cost

3. Agentic AI Insights
  *The AI agent analyzes pipeline data and produces:
  *Cost anomaly detection
  *Workflow optimization recommendations
  *Redundant build & stale branch identification
  *Predicted savings if failures reduce
  *Actionable guidance for engineering teams
  *This transforms raw CI/CD logs into dev-ready operational intelligence.

4. Slack Integration (Operational Reporting)
  *One-click Slack reporting includes:
  *Latest workflow runs
  *KPI metrics
  *Cost summaries
  *AI-generated insights
  *Provides automated updates for teams without opening the dashboard.

5. Visual Analytics
  *Interactive Plotly-based charts:
  *Success vs failure distribution
  *Cost distribution by branch
  *Trend analysis (cost over time)
  *Average build duration per repository

System Architecture
GitHub Actions → Data Collector → SQLite DB → Dashboard UI
                           ↓
                     Agentic AI Layer
                           ↓
                      Slack Reporting


Data Layer: Workflow metadata stored locally
Computation Layer: Durations, costs, anomalies, redundant build logic
AI Layer: Insight generator using OpenAI/Azure OpenAI
Presentation Layer: Streamlit UI + Plotly visualizations

