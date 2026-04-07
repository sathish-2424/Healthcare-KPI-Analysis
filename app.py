from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_PATH = Path(__file__).with_name("healthcare.csv")
MONEY_FMT = "${:,.0f}"


st.set_page_config(
    page_title="Healthcare KPI Analysis",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    date_cols = ["Date of Admission", "Discharge Date"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["Length of Stay"] = (
        df["Discharge Date"] - df["Date of Admission"]
    ).dt.days.clip(lower=0)
    df["Admission Month"] = df["Date of Admission"].dt.to_period("M").dt.to_timestamp()
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors="coerce")
    df["Billing Category"] = pd.cut(
        df["Billing Amount"],
        bins=[float("-inf"), 0, 10000, 25000, 40000, float("inf")],
        labels=["Negative", "$0-$10K", "$10K-$25K", "$25K-$40K", "$40K+"],
    )
    df["Age Group"] = pd.cut(
        df["Age"],
        bins=[0, 19, 40, 60, 120],
        labels=["Under 20", "20-40", "41-60", "60+"],
        right=True,
    )

    return df


def money(value: float) -> str:
    if pd.isna(value):
        return "$0"
    return MONEY_FMT.format(value)


def metric_delta(current: float, baseline: float, suffix: str = "") -> str | None:
    if pd.isna(current) or pd.isna(baseline) or baseline == 0:
        return None
    return f"{current - baseline:,.1f}{suffix} vs dataset avg"


def filter_multiselect(label: str, options: pd.Series, key: str) -> list[str]:
    sorted_options = sorted(options.dropna().unique())
    return st.sidebar.multiselect(label, sorted_options, default=sorted_options, key=key)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    min_date = df["Date of Admission"].min().date()
    max_date = df["Date of Admission"].max().date()
    date_range = st.sidebar.date_input(
        "Admission date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if len(date_range) != 2:
        st.sidebar.info("Select both a start and end date to filter admissions.")
        start_date, end_date = min_date, max_date
    else:
        start_date, end_date = date_range

    conditions = filter_multiselect("Medical condition", df["Medical Condition"], "condition")
    admission_types = filter_multiselect("Admission type", df["Admission Type"], "admission_type")
    insurers = filter_multiselect("Insurance provider", df["Insurance Provider"], "insurer")
    genders = filter_multiselect("Gender", df["Gender"], "gender")
    test_results = filter_multiselect("Test results", df["Test Results"], "test_results")

    billing_choice = st.sidebar.radio(
        "Billing records",
        ["All records", "Exclude negative billing"],
        horizontal=False,
    )

    st.sidebar.divider()
    st.sidebar.caption("High-cardinality filters")
    limit_hospitals = st.sidebar.checkbox("Limit to top hospitals by revenue", value=True)
    top_hospital_limit = st.sidebar.slider("Top hospital count", 5, 50, 20, 5)
    hospital_search = st.sidebar.text_input("Hospital name contains").strip()
    doctor_search = st.sidebar.text_input("Doctor name contains").strip()

    mask = (
        df["Date of Admission"].dt.date.between(start_date, end_date)
        & df["Medical Condition"].isin(conditions)
        & df["Admission Type"].isin(admission_types)
        & df["Insurance Provider"].isin(insurers)
        & df["Gender"].isin(genders)
        & df["Test Results"].isin(test_results)
    )

    if billing_choice == "Exclude negative billing":
        mask &= df["Billing Amount"] >= 0

    if limit_hospitals:
        top_hospitals = (
            df.groupby("Hospital", observed=True)["Billing Amount"]
            .sum()
            .nlargest(top_hospital_limit)
            .index
        )
        mask &= df["Hospital"].isin(top_hospitals)

    if hospital_search:
        mask &= df["Hospital"].str.contains(hospital_search, case=False, na=False)
    if doctor_search:
        mask &= df["Doctor"].str.contains(doctor_search, case=False, na=False)

    return df.loc[mask].copy()


def render_kpis(filtered: pd.DataFrame, full: pd.DataFrame) -> None:
    total_patients = len(filtered)
    total_revenue = filtered["Billing Amount"].sum()
    avg_billing = filtered["Billing Amount"].mean()
    avg_los = filtered["Length of Stay"].mean()
    abnormal_rate = (filtered["Test Results"].eq("Abnormal").mean() * 100)

    baseline_billing = full["Billing Amount"].mean()
    baseline_los = full["Length of Stay"].mean()
    baseline_abnormal = full["Test Results"].eq("Abnormal").mean() * 100

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Patients", f"{total_patients:,}")
    col2.metric("Revenue", money(total_revenue))
    col3.metric(
        "Avg billing",
        money(avg_billing),
        delta=metric_delta(avg_billing, baseline_billing),
    )
    col4.metric(
        "Avg stay",
        f"{avg_los:,.1f} days" if pd.notna(avg_los) else "0.0 days",
        delta=metric_delta(avg_los, baseline_los, " days"),
        delta_color="inverse",
    )
    col5.metric(
        "Abnormal tests",
        f"{abnormal_rate:,.1f}%" if pd.notna(abnormal_rate) else "0.0%",
        delta=metric_delta(abnormal_rate, baseline_abnormal, " pts"),
        delta_color="inverse",
    )


def render_empty_state() -> None:
    st.warning("No records match the current filters. Broaden the date range or search terms.")


def monthly_revenue_chart(df: pd.DataFrame) -> go.Figure:
    monthly = (
        df.groupby("Admission Month", observed=True)
        .agg(revenue=("Billing Amount", "sum"), patients=("Name", "count"))
        .reset_index()
        .sort_values("Admission Month")
    )
    monthly["3-month moving avg"] = monthly["revenue"].rolling(3, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=monthly["Admission Month"],
            y=monthly["revenue"],
            name="Revenue",
            marker_color="#1f77b4",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["Admission Month"],
            y=monthly["3-month moving avg"],
            name="3-month moving average",
            mode="lines",
            line=dict(color="#d62728", width=3),
        )
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Admission month",
        yaxis_title="Billing amount",
        hovermode="x unified",
        legend_orientation="h",
        legend_y=1.1,
    )
    return fig


def overview_tab(df: pd.DataFrame) -> None:
    st.subheader("Revenue and patient mix")
    st.plotly_chart(monthly_revenue_chart(df), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        age_summary = (
            df.groupby("Age Group", observed=True)
            .agg(revenue=("Billing Amount", "sum"), patients=("Name", "count"))
            .reset_index()
        )
        fig = px.bar(
            age_summary,
            x="Age Group",
            y="revenue",
            text="patients",
            color="Age Group",
            title="Revenue by age group",
            template="plotly_white",
        )
        fig.update_layout(showlegend=False, yaxis_title="Billing amount")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        admission_counts = df["Admission Type"].value_counts().reset_index()
        admission_counts.columns = ["Admission Type", "Patients"]
        fig = px.pie(
            admission_counts,
            names="Admission Type",
            values="Patients",
            hole=0.48,
            title="Admission type distribution",
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)


def financial_tab(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        hospital_revenue = (
            df.groupby("Hospital", observed=True)
            .agg(revenue=("Billing Amount", "sum"), patients=("Name", "count"))
            .sort_values("revenue", ascending=False)
            .head(15)
            .reset_index()
        )
        fig = px.bar(
            hospital_revenue,
            x="revenue",
            y="Hospital",
            color="patients",
            orientation="h",
            title="Top hospitals by revenue",
            template="plotly_white",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Billing amount")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        doctor_revenue = (
            df.groupby("Doctor", observed=True)
            .agg(revenue=("Billing Amount", "sum"), patients=("Name", "count"))
            .sort_values("revenue", ascending=False)
            .head(15)
            .reset_index()
        )
        fig = px.bar(
            doctor_revenue,
            x="revenue",
            y="Doctor",
            color="patients",
            orientation="h",
            title="Top doctors by revenue",
            template="plotly_white",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Billing amount")
        st.plotly_chart(fig, use_container_width=True)

    billing_mix = (
        df.groupby(["Insurance Provider", "Billing Category"], observed=True)
        .size()
        .reset_index(name="patients")
    )
    fig = px.bar(
        billing_mix,
        x="Insurance Provider",
        y="patients",
        color="Billing Category",
        title="Billing bands by insurance provider",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)


def clinical_tab(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        condition_summary = (
            df.groupby("Medical Condition", observed=True)
            .agg(
                patients=("Name", "count"),
                revenue=("Billing Amount", "sum"),
                avg_stay=("Length of Stay", "mean"),
                abnormal_rate=("Test Results", lambda s: s.eq("Abnormal").mean() * 100),
            )
            .reset_index()
            .sort_values("patients", ascending=False)
        )
        fig = px.scatter(
            condition_summary,
            x="avg_stay",
            y="revenue",
            size="patients",
            color="Medical Condition",
            hover_data={"abnormal_rate": ":.1f"},
            title="Condition performance",
            template="plotly_white",
        )
        fig.update_layout(xaxis_title="Average length of stay", yaxis_title="Billing amount")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        results_by_condition = (
            df.groupby(["Medical Condition", "Test Results"], observed=True)
            .size()
            .reset_index(name="patients")
        )
        fig = px.bar(
            results_by_condition,
            x="Medical Condition",
            y="patients",
            color="Test Results",
            title="Test results by condition",
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

    medication_summary = (
        df.groupby(["Medication", "Medical Condition"], observed=True)
        .size()
        .reset_index(name="patients")
    )
    fig = px.density_heatmap(
        medication_summary,
        x="Medication",
        y="Medical Condition",
        z="patients",
        histfunc="sum",
        title="Medication use by medical condition",
        template="plotly_white",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig, use_container_width=True)


def data_tab(df: pd.DataFrame, full: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Dataset rows", f"{len(full):,}")
    col2.metric("Filtered rows", f"{len(df):,}")
    col3.metric("Negative billing rows", f"{int((df['Billing Amount'] < 0).sum()):,}")

    st.subheader("Filtered records")
    st.dataframe(
        df.sort_values("Date of Admission", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv,
        file_name="filtered_healthcare_kpis.csv",
        mime="text/csv",
    )


def main() -> None:
    st.title("Healthcare KPI Analysis")
    st.caption(
        "An interactive healthcare KPI dashboard for monitoring hospital performance, "
        "patient trends, and revenue insights using real-world healthcare data. "
        "Use the filters and visualizations to track key indicators, analyze patient "
        "demographics, and identify opportunities to improve operational efficiency."
    )

    try:
        df = load_data()
    except FileNotFoundError:
        st.error(f"Could not find {DATA_PATH.name} next to app.py.")
        st.stop()

    filtered_df = apply_filters(df)
    render_kpis(filtered_df, df)

    st.divider()
    if filtered_df.empty:
        render_empty_state()
        st.stop()

    overview, financial, clinical, data = st.tabs(
        ["Overview", "Financial", "Clinical", "Data quality"]
    )
    with overview:
        overview_tab(filtered_df)
    with financial:
        financial_tab(filtered_df)
    with clinical:
        clinical_tab(filtered_df)
    with data:
        data_tab(filtered_df, df)


if __name__ == "__main__":
    main()
