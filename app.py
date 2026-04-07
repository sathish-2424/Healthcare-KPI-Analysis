import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="Healthcare KPI Dashboard", layout="wide")

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv('healthcare.csv')
    # Convert date columns
    df['Date of Admission'] = pd.to_datetime(df['Date of Admission'])
    df['Discharge Date'] = pd.to_datetime(df['Discharge Date'])
    # Calculate Length of Stay
    df['Length of Stay'] = (df['Discharge Date'] - df['Date of Admission']).dt.days
    # Extract Month/Year for time series
    df['MonthYear'] = df['Date of Admission'].dt.to_period('M').dt.to_timestamp()
    return df

try:
    df = load_data()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Dashboard Filters")
    
    hospitals = st.sidebar.multiselect("Select Hospital", options=df['Hospital'].unique(), default=df['Hospital'].unique()[:3])
    gender = st.sidebar.multiselect("Select Gender", options=df['Gender'].unique(), default=df['Gender'].unique())
    insurance = st.sidebar.multiselect("Select Insurance", options=df['Insurance Provider'].unique(), default=df['Insurance Provider'].unique())

    # Apply filters
    filtered_df = df[
        (df['Hospital'].isin(hospitals)) &
        (df['Gender'].isin(gender)) &
        (df['Insurance Provider'].isin(insurance))
    ]

    # --- MAIN TITLE ---
    st.title("🏥 Healthcare KPI Dashboard")
    st.markdown("--- ")

    # --- KPI METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = filtered_df['Billing Amount'].sum()
    total_patients = len(filtered_df)
    avg_billing = filtered_df['Billing Amount'].mean()
    avg_los = filtered_df['Length of Stay'].mean()

    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Total Patients", f"{total_patients:,}")
    col3.metric("Avg Billing", f"${avg_billing:,.2f}")
    col4.metric("Avg Length of Stay", f"{avg_los:.2f} Days")

    st.markdown("--- ")

    # --- VISUALIZATIONS ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Revenue by Age Group")
        filtered_df['Age Group'] = pd.cut(filtered_df['Age'], bins=[0, 18, 35, 50, 65, 100], labels=['0-18', '19-35', '36-50', '51-65', '65+'])
        age_revenue = filtered_df.groupby('Age Group')['Billing Amount'].sum().reset_index()
        fig_age = px.bar(age_revenue, x='Age Group', y='Billing Amount', color='Age Group', template='plotly_white')
        st.plotly_chart(fig_age, use_container_width=True)

    with row1_col2:
        st.subheader("Admission Type Distribution")
        fig_adm = px.pie(filtered_df, names='Admission Type', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_adm, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("Hospital-wise Billing Performance")
        hosp_billing = filtered_df.groupby('Hospital')['Billing Amount'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_hosp = px.bar(hosp_billing, y='Hospital', x='Billing Amount', orientation='h', template='plotly_dark')
        st.plotly_chart(fig_hosp, use_container_width=True)

    with row2_col2:
        st.subheader("Medical Condition Analysis")
        cond_counts = filtered_df['Medical Condition'].value_counts().reset_index()
        fig_cond = px.funnel(cond_counts, x='count', y='Medical Condition')
        st.plotly_chart(fig_cond, use_container_width=True)

    # --- TIME SERIES ANALYSIS ---
    st.subheader("Monthly Revenue Trends & Moving Average")
    monthly_revenue = filtered_df.groupby('MonthYear')['Billing Amount'].sum().reset_index()
    monthly_revenue['Moving Average'] = monthly_revenue['Billing Amount'].rolling(window=3).mean()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=monthly_revenue['MonthYear'], y=monthly_revenue['Billing Amount'], name='Monthly Revenue', line=dict(color='firebrick', width=4)))
    fig_trend.add_trace(go.Scatter(x=monthly_revenue['MonthYear'], y=monthly_revenue['Moving Average'], name='3-Month Moving Avg', line=dict(color='royalblue', width=4, dash='dash')))
    fig_trend.update_layout(template='plotly_white', xaxis_title='Date', yaxis_title='Revenue ($)')
    st.plotly_chart(fig_trend, use_container_width=True)

except FileNotFoundError:
    st.error("Please make sure 'healthcare.csv' is in the same directory as the script.")