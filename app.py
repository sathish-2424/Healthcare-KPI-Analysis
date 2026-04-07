import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Healthcare KPI Analysis",
    page_icon="H",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv("healthcare.csv")
    data["Date of Admission"] = pd.to_datetime(data["Date of Admission"], errors="coerce")
    data["Discharge Date"] = pd.to_datetime(data["Discharge Date"], errors="coerce")
    data["Billing Amount"] = pd.to_numeric(data["Billing Amount"], errors="coerce")
    data["Length of Stay"] = (
        data["Discharge Date"] - data["Date of Admission"]
    ).dt.days
    data["Age Category"] = pd.cut(
        data["Age"],
        bins=[0, 20, 40, 60, 120],
        labels=["Below 20", "20-40", "41-60", "60+"],
        include_lowest=True,
    )
    data["Admission Month"] = data["Date of Admission"].dt.to_period("M").astype(str)
    return data


def format_currency(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:,.2f}"


def apply_multiselect_filter(
    data: pd.DataFrame,
    column: str,
    label: str,
) -> pd.DataFrame:
    options = sorted(data[column].dropna().unique())
    selected = st.sidebar.multiselect(label, options=options, default=options)
    if not selected:
        return data.iloc[0:0]
    return data[data[column].isin(selected)]


df = load_data()

st.title("Healthcare KPI Analysis Dashboard")
st.markdown(
    """
    Designed and developed an interactive Healthcare KPI Analysis Dashboard to monitor
    hospital performance, patient trends, and revenue insights using real-world
    healthcare data.

    This dashboard helps stakeholders track key performance indicators, analyze
    patient demographics, and improve operational efficiency through data-driven
    decision making.
    """
)

st.sidebar.header("Dashboard Filters")
filtered_df = df.copy()
filtered_df = apply_multiselect_filter(filtered_df, "Hospital", "Hospital")
filtered_df = apply_multiselect_filter(filtered_df, "Gender", "Gender")
filtered_df = apply_multiselect_filter(
    filtered_df,
    "Insurance Provider",
    "Insurance Provider",
)
filtered_df = apply_multiselect_filter(
    filtered_df,
    "Admission Type",
    "Admission Type",
)

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

total_revenue = filtered_df["Billing Amount"].sum()
total_patients = filtered_df["Name"].count()
avg_billing = filtered_df["Billing Amount"].mean()
avg_stay = filtered_df["Length of Stay"].mean()

metric_cols = st.columns(4)
metric_cols[0].metric("Total Revenue", format_currency(total_revenue))
metric_cols[1].metric("Total Patients", f"{total_patients:,}")
metric_cols[2].metric("Average Billing", format_currency(avg_billing))
metric_cols[3].metric("Average Length of Stay", f"{avg_stay:.2f} days")

st.divider()

left_col, right_col = st.columns(2)

revenue_by_age = (
    filtered_df.groupby("Age Category", observed=True)["Billing Amount"]
    .sum()
    .reset_index()
)
left_col.plotly_chart(
    px.bar(
        revenue_by_age,
        x="Age Category",
        y="Billing Amount",
        title="Revenue by Age Category",
        text_auto=".2s",
        color="Age Category",
    ),
    use_container_width=True,
)

admission_type_count = (
    filtered_df["Admission Type"].value_counts().reset_index()
)
admission_type_count.columns = ["Admission Type", "Patients"]
right_col.plotly_chart(
    px.pie(
        admission_type_count,
        names="Admission Type",
        values="Patients",
        title="Patient Admissions by Type",
        hole=0.45,
    ),
    use_container_width=True,
)

left_col, right_col = st.columns(2)

hospital_revenue = (
    filtered_df.groupby("Hospital")["Billing Amount"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
left_col.plotly_chart(
    px.bar(
        hospital_revenue,
        x="Billing Amount",
        y="Hospital",
        orientation="h",
        title="Top 10 Hospitals by Billing Amount",
        text_auto=".2s",
    ).update_layout(yaxis={"categoryorder": "total ascending"}),
    use_container_width=True,
)

doctor_revenue = (
    filtered_df.groupby("Doctor")["Billing Amount"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
right_col.plotly_chart(
    px.bar(
        doctor_revenue,
        x="Billing Amount",
        y="Doctor",
        orientation="h",
        title="Top 10 Doctors by Billing Amount",
        text_auto=".2s",
    ).update_layout(yaxis={"categoryorder": "total ascending"}),
    use_container_width=True,
)

left_col, right_col = st.columns(2)

condition_revenue = (
    filtered_df.groupby("Medical Condition")["Billing Amount"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
left_col.plotly_chart(
    px.bar(
        condition_revenue,
        x="Medical Condition",
        y="Billing Amount",
        title="Billing Amount by Medical Condition",
        text_auto=".2s",
        color="Medical Condition",
    ),
    use_container_width=True,
)

gender_count = filtered_df["Gender"].value_counts().reset_index()
gender_count.columns = ["Gender", "Patients"]
right_col.plotly_chart(
    px.bar(
        gender_count,
        x="Gender",
        y="Patients",
        title="Patient Demographics by Gender",
        text_auto=True,
        color="Gender",
    ),
    use_container_width=True,
)

monthly_revenue = (
    filtered_df.groupby("Admission Month")["Billing Amount"]
    .sum()
    .reset_index()
    .sort_values("Admission Month")
)
st.plotly_chart(
    px.line(
        monthly_revenue,
        x="Admission Month",
        y="Billing Amount",
        title="Monthly Revenue Trend",
        markers=True,
    ),
    use_container_width=True,
)

with st.expander("View Filtered Healthcare Records"):
    st.dataframe(
        filtered_df[
            [
                "Name",
                "Age",
                "Gender",
                "Medical Condition",
                "Date of Admission",
                "Discharge Date",
                "Hospital",
                "Insurance Provider",
                "Admission Type",
                "Billing Amount",
                "Length of Stay",
            ]
        ],
        use_container_width=True,
    )
