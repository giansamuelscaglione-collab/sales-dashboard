import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR-K2bPgkFpcavReVoXH-K4HQWy6QxN12o6jWB5ywewq32TEo0qG9JaZpJgCMkVOiNTZB5P0Rp3UnuL/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Job Search Auto-Tracker", layout="wide")
st.title("Job Search Auto-Tracker")

if st.button("Refresh data"):
    st.cache_data.clear()

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    return df

df = load_data()
st.dataframe(df)
# --- 1. Status funnel ---
st.subheader("Application Funnel")
funnel_order = ["No Response Yet", "Application Confirmed", "Interview Request", "Offer", "Rejected"]
status_counts = df["Status"].value_counts().reindex(funnel_order, fill_value=0)

fig1, ax1 = plt.subplots(figsize=(7, 4))
ax1.bar(status_counts.index, status_counts.values, color="#4C7FA0")
ax1.set_ylabel("Applications")
plt.xticks(rotation=20)
st.pyplot(fig1)

# --- 2. Fit score distribution ---
st.subheader("AI Fit Score Distribution")
scores = pd.to_numeric(df["AI Fit Score"], errors="coerce").dropna()
if len(scores) > 0:
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.hist(scores, bins=10, color="#6B9B6E", edgecolor="white")
    ax2.set_xlabel("Fit Score")
    ax2.set_ylabel("Count")
    st.pyplot(fig2)
else:
    st.info("No fit scores yet.")

# --- 3. Calibration: fit score bucket vs outcome ---
st.subheader("Does a higher Fit Score predict a better outcome?")

def bucket_score(score):
    if score <= 40:
        return "Low (0-40)"
    elif score <= 70:
        return "Medium (41-70)"
    else:
        return "High (71-100)"

cal_df = df.copy()
cal_df["AI Fit Score"] = pd.to_numeric(cal_df["AI Fit Score"], errors="coerce")
cal_df = cal_df.dropna(subset=["AI Fit Score"])
cal_df["Score Bucket"] = cal_df["AI Fit Score"].apply(bucket_score)

positive_outcomes = {"Interview Request", "Offer"}
negative_outcomes = {"Rejected"}

summary_rows = []
for bucket in ["Low (0-40)", "Medium (41-70)", "High (71-100)"]:
    bucket_df = cal_df[cal_df["Score Bucket"] == bucket]
    total = len(bucket_df)
    if total == 0:
        continue
    positive = bucket_df["Status"].isin(positive_outcomes).sum()
    negative = bucket_df["Status"].isin(negative_outcomes).sum()
    pending = total - positive - negative
    summary_rows.append({
        "Score Bucket": bucket,
        "Total": total,
        "Interview/Offer %": round(100 * positive / total, 1),
        "Rejected %": round(100 * negative / total, 1),
        "Still Pending %": round(100 * pending / total, 1),
    })

summary_df = pd.DataFrame(summary_rows)

if len(summary_df) > 0:
    fig3, ax3 = plt.subplots(figsize=(7, 4))
    summary_df.set_index("Score Bucket")[["Interview/Offer %", "Rejected %", "Still Pending %"]].plot(
        kind="bar", stacked=True, ax=ax3, color=["#4C9A6B", "#C65A52", "#B0B0B0"]
    )
    plt.xticks(rotation=0)
    ax3.set_ylabel("% of applications")
    st.pyplot(fig3)
    st.caption(
        "With only a handful of applications so far, most outcomes are still pending — "
        "this chart will become a more meaningful test of the fit score as real responses come in."
    )
else:
    st.info("Not enough scored data yet for calibration.")

# --- 4. Recent updates table ---
st.subheader("Recently Updated")
if "Last Updated" in df.columns:
    recent = df.sort_values("Last Updated", ascending=False).head(5)
else:
    recent = df.head(5)
st.dataframe(recent[["Company", "Role", "Status", "AI Fit Score", "Last Updated"]])
