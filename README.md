# 🛒 E-Commerce Insights Hub

A natural-language analytics app built with **Databricks Genie** and **Databricks Apps**.
Business users ask questions in plain English about orders, customers, delivery and
review sentiment, and get a text answer, a results table and the SQL that Genie generated.

## Use case

E-commerce teams often depend on analysts to answer simple business questions.
This app lets non-technical users query the Olist e-commerce dataset directly,
for example revenue by category, review sentiment trends, or the effect of late
deliveries on review scores.

## Demo

- Demo video: (https://drive.google.com/file/d/1OStjCS2J_H-0YfzMz5-dDx-EM-kuTDk2/view?usp=sharing)

> Databricks Apps require sign-in to the workspace and do not support public links,
> so a recorded demo is provided instead of a live URL.

## Architecture

- **Data:** Olist e-commerce dataset stored in Unity Catalog (`workspace.olist`),
  with a curated gold table (`gold_order_insights`) for analytics
- **Genie space:** configured over the gold tables
- **App:** Streamlit app deployed on Databricks Apps
- **Integration:** the Databricks SDK starts and continues Genie conversations
- **Security:** the app runs as its own service principal with only the access it needs

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface and Genie API calls |
| `app.yaml` | App start command and Genie space environment variable |
| `requirements.txt` | Python packages |

## Setup

1. Load the Olist data into Unity Catalog and build the gold tables.
2. Create a Genie space over those tables.
3. In Databricks, create an app (Streamlit) and upload these files as its source.
4. Add the Genie space as an app resource with the resource key `genie-space`.
5. Grant the app's service principal:
   - `USE CATALOG`, `USE SCHEMA` and `SELECT` on the schema
   - `CAN USE` on the SQL warehouse
6. Deploy the app and open its URL.

## Example questions

- What are the top 10 product categories by revenue?
- Show average sentiment stars by month
- Compare average order value by customer tier
- Which categories have the most negative reviews?
- Do late deliveries get lower review scores? Show by state

## Challenges and fixes

- **PERMISSION_DENIED from Genie:** surfaced Genie's real error message in the app,
  found the service principal lacked table access, and fixed it with `GRANT` statements.
- **SDK version differences:** some Genie SDK methods differed between versions, so the
  result-fetching code checks for several method names.
- **Free Edition limits:** Genie rate limits and slower follow-up questions on
  serverless compute.

## Tech stack

Databricks Genie, Databricks Apps, Unity Catalog, Python, Streamlit, Databricks SDK, pandas
