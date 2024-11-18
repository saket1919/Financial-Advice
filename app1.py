import streamlit as st
import finnhub
import os
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd

# Load environment variables
load_dotenv()

# Access the API key from the environment variable
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

if not FINNHUB_API_KEY:
    st.error("API Key not found. Please set it in the environment variable 'FINNHUB_API_KEY'.")
    st.stop()

# Initialize Finnhub Client
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

# Fetch company profile
def fetch_company_profile(ticker):
    try:
        profile = finnhub_client.company_profile2(symbol=ticker)
        return profile
    except Exception as e:
        return {"error": f"Error fetching company profile: {e}"}

# Fetch detailed metrics
def fetch_detailed_metrics(ticker):
    try:
        metrics = finnhub_client.company_basic_financials(symbol=ticker, metric="all")
        if "metric" not in metrics or not metrics["metric"]:
            return {"error": "No metrics available for this ticker"}
        return metrics["metric"]
    except Exception as e:
        return {"error": str(e)}

# Fetch analyst recommendations
def fetch_recommendations(ticker):
    try:
        recommendations = finnhub_client.recommendation_trends(symbol=ticker)
        if not recommendations:
            return {"error": "No recommendations available"}
        return recommendations
    except Exception as e:
        return {"error": str(e)}

# Streamlit App Layout
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("📊 Financial Investment Dashboard")

# Sidebar for inputs
st.sidebar.header("Input Options")
ticker = st.sidebar.text_input("Enter Company Ticker (e.g., AAPL)").upper().strip()
chart_type = st.sidebar.selectbox("Select Chart Type", ["Bar", "Line", "Pie"])
download_option = st.sidebar.checkbox("Enable Data Download")

# Generate Result Button
if st.sidebar.button("Generate Result"):
    if not ticker:
        st.sidebar.error("Please enter a valid company ticker.")
    else:
        # Loading animation with professional UI
        with st.spinner(f"Fetching data for {ticker}, please wait..."):
            profile = fetch_company_profile(ticker)
            metrics = fetch_detailed_metrics(ticker)
            recommendations = fetch_recommendations(ticker)

        # Display results in tabs
        tabs = st.tabs(["📄 Profile", "📊 Metrics", "📈 Recommendations", "💡 Insights"])

        # Profile Tab
        with tabs[0]:
            if "error" in profile:
                st.error(profile["error"])
            else:
                st.subheader("Company Profile")
                profile_data = {
                    "Name": profile.get("name", "N/A"),
                    "Ticker": profile.get("ticker", "N/A"),
                    "Industry": profile.get("finnhubIndustry", "N/A"),
                    "Country": profile.get("country", "N/A"),
                    "Exchange": profile.get("exchange", "N/A"),
                    "Market Cap (in Billion)": f'{profile.get("marketCapitalization", 0):,.2f}',
                    "Share Outstanding": f'{profile.get("shareOutstanding", 0):,.2f}',
                }

                st.table(
                    [{"Field": key, "Value": value} for key, value in profile_data.items()]
                )
                if profile.get("logo"):
                    st.image(profile["logo"], width=100)
                if profile.get("weburl"):
                    st.markdown(f"[Visit Website]({profile['weburl']})", unsafe_allow_html=True)

        # Metrics Tab
        with tabs[1]:
            if "error" in metrics:
                st.error(metrics["error"])
            else:
                st.subheader("Key Metrics")
                income_data = {
                    "Revenue Per Share": metrics.get("revenuePerShareAnnual", "N/A"),
                    "Net Income": metrics.get("netIncomeAnnual", "N/A"),
                }
                balance_data = {
                    "Total Assets": metrics.get("totalAssets", "N/A"),
                    "Total Liabilities": metrics.get("totalLiabilities", "N/A"),
                }
                valuation_data = {
                    "P/E Ratio": metrics.get("peNormalizedAnnual", "N/A"),
                    "EV/EBITDA": metrics.get("enterpriseValueOverEBITDA", "N/A"),
                }

                st.write("**Income Statement**")
                st.table(income_data)
                st.write("**Balance Sheet**")
                st.table(balance_data)
                st.write("**Valuation Metrics**")
                st.table(valuation_data)

                # Chart Visualization
                if chart_type:
                    chart_data = pd.DataFrame({
                        "Metric": list(income_data.keys()),
                        "Value": [v if isinstance(v, (int, float)) else 0 for v in income_data.values()]
                    })
                    if chart_type == "Bar":
                        fig = px.bar(chart_data, x="Metric", y="Value", title="Income Metrics")
                    elif chart_type == "Line":
                        fig = px.line(chart_data, x="Metric", y="Value", title="Income Metrics")
                    elif chart_type == "Pie":
                        fig = px.pie(chart_data, names="Metric", values="Value", title="Income Metrics")
                    st.plotly_chart(fig)

        # Recommendations Tab
        with tabs[2]:
            if "error" in recommendations:
                st.error(recommendations["error"])
            else:
                st.subheader("Analyst Recommendations")
                buy = sum([rec["buy"] for rec in recommendations])
                hold = sum([rec["hold"] for rec in recommendations])
                sell = sum([rec["sell"] for rec in recommendations])

                st.write(f"**Buy**: {buy}, **Hold**: {hold}, **Sell**: {sell}")
                fig = px.bar(
                    x=["Buy", "Hold", "Sell"],
                    y=[buy, hold, sell],
                    title="Analyst Recommendations",
                    labels={"x": "Recommendation", "y": "Count"},
                )
                st.plotly_chart(fig)

        # Insights Tab
        with tabs[3]:
            st.subheader("Actionable Insights")
            if buy > sell and buy > hold:
                st.success("Strong Buy")
            elif hold > buy and hold > sell:
                st.info("Hold")
            elif sell > buy and sell > hold:
                st.error("Sell")
            else:
                st.warning("No clear recommendation")

        # Data Download
        if download_option and "error" not in metrics:
            metrics_data = pd.DataFrame({
                "Metric": list(metrics.keys()),
                "Value": list(metrics.values()),
            })
            st.sidebar.download_button(
                "Download Metrics",
                metrics_data.to_csv(index=False),
                file_name=f"{ticker}_metrics.csv",
                mime="text/csv",
            )
