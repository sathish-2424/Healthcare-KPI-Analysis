from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_FILE = Path(__file__).with_name("healthcare.csv")
AGE_BINS = [0, 20, 40, 60, 120]
AGE_LABELS = ["Below 20", "20-40", "41-60", "60+"]


st.set_page_config(
    page_title="Healthcare KPI Analysis Dashboard",
    page_icon=":hospital:",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)

    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors="coerce")
    df["Date of Admission"] = pd.to_datetime(df["Date of Admission"], errors="coerce")
    df["Discharge Date"] = pd.to_datetime(df["Discharge Date"], errors="coerce")
    df["Length of Stay"] = (
        df["Discharge Date"] - df["Date of Admission"]
    ).dt.days.clip(lower=0)
    df["Month"] = df["Date of Admission"].dt.to_period("M").dt.to_timestamp()
    df["Age Category"] = pd.cut(
        df["Age"],
        bins=AGE_BINS,
        labels=AGE_LABELS,
        right=True,
        include_lowest=True,
    )

    return df.dropna(subset=["Date of Admission", "Discharge Date"])


def format_currency(value: float) -> str:
    if pd.isna(value):
        return "$0"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:,.2f}"


def metric_value(value: float, suffix: str = "") -> str:
    if pd.isna(value):
        return f"0{suffix}"
    return f"{value:,.2f}{suffix}"


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Dashboard Filters")

    min_date = df["Date of Admission"].min().date()
    max_date = df["Date of Admission"].max().date()
    top_hospitals = (
        df.groupby("Hospital")["Billing Amount"]
        .sum()
        .sort_values(ascending=False)
        .head(25)
        .index.tolist()
    )

    date_range = st.sidebar.date_input(
        "Admission Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    hospital_search = st.sidebar.text_input(
        "Search Hospital Name",
        placeholder="Type part of a hospital name",
    )
    focus_hospitals = st.sidebar.multiselect(
        "Focus Hospital",
        options=top_hospitals,
        default=[],
        help="Optional list of the top 25 hospitals by revenue.",
    )
    genders = st.sidebar.multiselect(
        "Gender",
        options=sorted(df["Gender"].dropna().unique()),
        default=sorted(df["Gender"].dropna().unique()),
    )
    insurance_providers = st.sidebar.multiselect(
        "Insurance Provider",
        options=sorted(df["Insurance Provider"].dropna().unique()),
        default=sorted(df["Insurance Provider"].dropna().unique()),
    )
    admission_types = st.sidebar.multiselect(
        "Admission Type",
        options=sorted(df["Admission Type"].dropna().unique()),
        default=sorted(df["Admission Type"].dropna().unique()),
    )

    if len(date_range) != 2:
        start_date, end_date = min_date, max_date
    else:
        start_date, end_date = date_range

    mask = (
        df["Gender"].isin(genders)
        & df["Insurance Provider"].isin(insurance_providers)
        & df["Admission Type"].isin(admission_types)
        & (df["Date of Admission"].dt.date >= start_date)
        & (df["Date of Admission"].dt.date <= end_date)
    )

    if hospital_search:
        mask &= df["Hospital"].str.contains(hospital_search, case=False, na=False)

    if focus_hospitals:
        mask &= df["Hospital"].isin(focus_hospitals)

    return df.loc[mask].copy()


def show_kpis(df: pd.DataFrame) -> None:
    total_revenue = df["Billing Amount"].sum()
    total_patients = len(df)
    avg_billing = df["Billing Amount"].mean()
    avg_length_of_stay = df["Length of Stay"].mean()
    unique_hospitals = df["Hospital"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", format_currency(total_revenue))
    col2.metric("Total Patients", f"{total_patients:,}")
    col3.metric("Average Billing", format_currency(avg_billing))
    col4.metric("Average Stay", metric_value(avg_length_of_stay, " days"))
    col5.metric("Hospitals", f"{unique_hospitals:,}")


def revenue_trend_chart(df: pd.DataFrame) -> None:
    monthly_revenue = (
        df.groupby("Month", as_index=False)["Billing Amount"].sum().sort_values("Month")
    )
    monthly_revenue["3-Month Moving Average"] = monthly_revenue[
        "Billing Amount"
    ].rolling(window=3, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly_revenue["Month"],
            y=monthly_revenue["Billing Amount"],
            mode="lines+markers",
            name="Monthly Revenue",
            line={"color": "#0f766e", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly_revenue["Month"],
            y=monthly_revenue["3-Month Moving Average"],
            mode="lines",
            name="3-Month Moving Average",
            line={"color": "#dc2626", "width": 3, "dash": "dash"},
        )
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_title="Admission Month",
        yaxis_title="Revenue",
        legend_title_text="",
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.title("Healthcare KPI Analysis Dashboard")
    st.caption(
        "Monitor hospital performance, patient trends, and revenue insights using "
        "real-world healthcare data."
    )

    try:
        df = load_data()
    except FileNotFoundError:
        st.error(f"Could not find `{DATA_FILE.name}` in the project folder.")
        st.stop()

    filtered_df = sidebar_filters(df)

    if filtered_df.empty:
        st.warning("No records match the selected filters. Adjust the filters to continue.")
        st.stop()

    show_kpis(filtered_df)

    st.divider()

    trend_tab, performance_tab, patient_tab = st.tabs(
        ["Revenue Trends", "Hospital Performance", "Patient Insights"]
    )

    with trend_tab:
        st.subheader("Monthly Revenue Trend")
        revenue_trend_chart(filtered_df)

        col1, col2 = st.columns(2)
        with col1:
            age_revenue = (
                filtered_df.groupby("Age Category", observed=False)["Billing Amount"]
                .sum()
                .reset_index()
            )
            fig = px.bar(
                age_revenue,
                x="Age Category",
                y="Billing Amount",
                title="Revenue by Age Category",
                color="Age Category",
                template="plotly_white",
            )
            fig.update_layout(showlegend=False, margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            condition_revenue = (
                filtered_df.groupby("Medical Condition", as_index=False)["Billing Amount"]
                .sum()
                .sort_values("Billing Amount", ascending=False)
            )
            fig = px.bar(
                condition_revenue,
                x="Billing Amount",
                y="Medical Condition",
                title="Revenue by Medical Condition",
                orientation="h",
                template="plotly_white",
                color="Billing Amount",
                color_continuous_scale="Teal",
            )
            fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

    with performance_tab:
        col1, col2 = st.columns(2)

        with col1:
            hospital_revenue = (
                filtered_df.groupby("Hospital", as_index=False)["Billing Amount"]
                .sum()
                .sort_values("Billing Amount", ascending=False)
                .head(10)
            )
            fig = px.bar(
                hospital_revenue,
                x="Billing Amount",
                y="Hospital",
                title="Top Hospitals by Billing Revenue",
                orientation="h",
                template="plotly_white",
                color="Billing Amount",
                color_continuous_scale="Blues",
            )
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            doctor_revenue = (
                filtered_df.groupby("Doctor", as_index=False)["Billing Amount"]
                .sum()
                .sort_values("Billing Amount", ascending=False)
                .head(10)
            )
            fig = px.bar(
                doctor_revenue,
                x="Billing Amount",
                y="Doctor",
                title="Top Doctors by Billing Revenue",
                orientation="h",
                template="plotly_white",
                color="Billing Amount",
                color_continuous_scale="Greens",
            )
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detailed Hospital KPI View")
        hospital_summary = (
            filtered_df.groupby("Hospital")
            .agg(
                Patients=("Name", "count"),
                Revenue=("Billing Amount", "sum"),
                Average_Billing=("Billing Amount", "mean"),
                Average_Length_of_Stay=("Length of Stay", "mean"),
            )
            .sort_values("Revenue", ascending=False)
            .reset_index()
        )
        st.dataframe(
            hospital_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Revenue": st.column_config.NumberColumn(format="$%.2f"),
                "Average_Billing": st.column_config.NumberColumn(format="$%.2f"),
                "Average_Length_of_Stay": st.column_config.NumberColumn(format="%.2f days"),
            },
        )

    with patient_tab:
        col1, col2, col3 = st.columns(3)

        with col1:
            fig = px.pie(
                filtered_df,
                names="Admission Type",
                title="Admission Type Distribution",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(
                filtered_df,
                names="Gender",
                title="Patient Gender Mix",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        with col3:
            insurance_counts = (
                filtered_df["Insurance Provider"].value_counts().reset_index()
            )
            insurance_counts.columns = ["Insurance Provider", "Patients"]
            fig = px.bar(
                insurance_counts,
                x="Insurance Provider",
                y="Patients",
                title="Patients by Insurance Provider",
                template="plotly_white",
                color="Patients",
                color_continuous_scale="Oranges",
            )
            fig.update_layout(margin={"l": 20, "r": 20, "t": 50, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Patient Records")
        st.dataframe(
            filtered_df[
                [
                    "Name",
                    "Age",
                    "Gender",
                    "Medical Condition",
                    "Date of Admission",
                    "Hospital",
                    "Doctor",
                    "Insurance Provider",
                    "Billing Amount",
                    "Admission Type",
                    "Length of Stay",
                ]
            ].sort_values("Date of Admission", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Billing Amount": st.column_config.NumberColumn(format="$%.2f"),
                "Date of Admission": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Length of Stay": st.column_config.NumberColumn(format="%d days"),
            },
        )


if __name__ == "__main__":
    main()
