import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="Healthcare KPI Dashboard", layout="wide")

st.title("🏥 Healthcare KPI Analysis")

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("healthcare.csv")
    df.columns = df.columns.str.strip()  # clean column names
    return df

df = load_data()

# ---------------------------
# Data Preprocessing
# ---------------------------
# Convert date columns
df["Date of Admission"] = pd.to_datetime(df["Date of Admission"], errors='coerce')
df["Discharge Date"] = pd.to_datetime(df["Discharge Date"], errors='coerce')

# Create Length of Stay (LOS)
df["Length of Stay"] = (df["Discharge Date"] - df["Date of Admission"]).dt.days

# Drop null important values
df = df.dropna(subset=["Billing Amount", "Date of Admission"])

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("Filters")

hospital = st.sidebar.multiselect(
    "Select Hospital",
    options=df["Hospital"].dropna().unique(),
    default=df["Hospital"].dropna().unique()
)

gender = st.sidebar.multiselect(
    "Select Gender",
    options=df["Gender"].dropna().unique(),
    default=df["Gender"].dropna().unique()
)

insurance = st.sidebar.multiselect(
    "Insurance Provider",
    options=df["Insurance Provider"].dropna().unique(),
    default=df["Insurance Provider"].dropna().unique()
)

# Apply filters
df_filtered = df[
    (df["Hospital"].isin(hospital)) &
    (df["Gender"].isin(gender)) &
    (df["Insurance Provider"].isin(insurance))
].copy()

# ---------------------------
# KPI Metrics
# ---------------------------
total_revenue = df_filtered["Billing Amount"].sum()
total_patients = df_filtered.shape[0]
avg_billing = df_filtered["Billing Amount"].mean()
avg_los = df_filtered["Length of Stay"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Total Revenue", f"{total_revenue/1e9:.2f} bn")
col2.metric("👥 Total Patients", f"{total_patients/1000:.0f}K")
col3.metric("📊 Avg Billing", f"{avg_billing:.2f}")
col4.metric("🛏 Avg Length of Stay", f"{avg_los:.2f} days")

# ---------------------------
# 📈 Monthly Revenue Trend
# ---------------------------
st.subheader("📈 Monthly Revenue Trend")

df_filtered["YearMonth"] = df_filtered["Date of Admission"].dt.to_period("M").astype(str)

monthly_revenue = (
    df_filtered.groupby("YearMonth")["Billing Amount"]
    .sum()
    .reset_index()
    .sort_values("YearMonth")
)

# Moving Average
monthly_revenue["MA_3"] = monthly_revenue["Billing Amount"].rolling(3).mean()

fig_ts = px.line(
    monthly_revenue,
    x="YearMonth",
    y=["Billing Amount", "MA_3"],
    title="Revenue Trend with Moving Average",
    markers=True
)

st.plotly_chart(fig_ts, use_container_width=True)

# ---------------------------
# Charts Row 1
# ---------------------------
col1, col2, col3 = st.columns(3)

# Age Group
age_bins = [0, 20, 40, 60, 100]
labels = ["Below 20", "20-40", "41-60", "60+"]

df_filtered["Age Group"] = pd.cut(df_filtered["Age"], bins=age_bins, labels=labels)

age_rev = df_filtered.groupby("Age Group")["Billing Amount"].sum().reset_index()

fig1 = px.pie(age_rev, names="Age Group", values="Billing Amount", title="Revenue by Age Category")
col1.plotly_chart(fig1, use_container_width=True)

# Admission Type
admission = df_filtered["Admission Type"].value_counts().reset_index()
admission.columns = ["Admission Type", "Count"]

fig2 = px.pie(admission, names="Admission Type", values="Count", title="Admission Type Distribution")
col2.plotly_chart(fig2, use_container_width=True)

# Hospital Billing
hospital_bill = df_filtered.groupby("Hospital")["Billing Amount"].sum().reset_index()

fig3 = px.bar(
    hospital_bill.sort_values(by="Billing Amount", ascending=False).head(5),
    x="Billing Amount",
    y="Hospital",
    orientation='h',
    title="Top Hospitals by Billing"
)
col3.plotly_chart(fig3, use_container_width=True)

# ---------------------------
# Charts Row 2
# ---------------------------
col1, col2 = st.columns(2)

# Doctor Billing
doctor_bill = df_filtered.groupby("Doctor")["Billing Amount"].sum().reset_index()

fig4 = px.bar(
    doctor_bill.sort_values(by="Billing Amount", ascending=False).head(5),
    x="Billing Amount",
    y="Doctor",
    orientation='h',
    title="Top Doctors by Billing"
)
col1.plotly_chart(fig4, use_container_width=True)

# Medical Condition
condition_bill = df_filtered.groupby("Medical Condition")["Billing Amount"].sum().reset_index()

fig5 = px.bar(
    condition_bill.sort_values(by="Billing Amount", ascending=False),
    x="Billing Amount",
    y="Medical Condition",
    orientation='h',
    title="Billing by Medical Condition"
)
col2.plotly_chart(fig5, use_container_width=True)

# ---------------------------
# Insights Section
# ---------------------------
st.subheader("📌 Key Insights")

top_age = age_rev.sort_values(by="Billing Amount", ascending=False).iloc[0]["Age Group"]
top_condition = condition_bill.sort_values(by="Billing Amount", ascending=False).iloc[0]["Medical Condition"]
top_hospital = hospital_bill.sort_values(by="Billing Amount", ascending=False).iloc[0]["Hospital"]

st.write(f"• Highest revenue comes from **{top_age}** age group")
st.write(f"• Top contributing medical condition is **{top_condition}**")
st.write(f"• Top performing hospital is **{top_hospital}**")
st.write("• Revenue trends show monthly variation and patterns")
st.write("• Chronic diseases contribute significantly to revenue")