-- Total Revenue
SELECT
  COUNT(*) AS total_admissions,
  SUM(Billing_Amount) AS total_revenue,
  AVG(Billing_Amount) AS avg_billing,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY Billing_Amount) AS median_billing
FROM healthcare;

-- Revenue trends by month (monthly revenue and admission count)
SELECT
  DATE_TRUNC('month', Date_of_Admission)::date AS month,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY 1
ORDER BY 1;

-- Revenue trends by year
SELECT
  EXTRACT(YEAR FROM Date_of_Admission)::int AS year,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY 1
ORDER BY 1;

-- Admissions by type and average billing
SELECT
  Admission_Type,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY Admission_Type
ORDER BY revenue DESC;

-- Hospital performance (top 10 by revenue)
SELECT
  Hospital,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY Hospital
ORDER BY revenue DESC
LIMIT 10;

-- Doctor performance (by revenue and admissions)
SELECT
  Doctor,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY Doctor
ORDER BY revenue DESC
LIMIT 10;

-- Patient segmentation by age groups (buckets) with avg billing
SELECT
  CASE
    WHEN Age < 18 THEN '0-17'
    WHEN Age BETWEEN 18 AND 34 THEN '18-34'
    WHEN Age BETWEEN 35 AND 54 THEN '35-54'
    WHEN Age BETWEEN 55 AND 74 THEN '55-74'
    ELSE '75+'
  END AS age_group,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY age_group
ORDER BY age_group;

-- Admissions by medical condition (top conditions)
SELECT
  Medical_Condition,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY Medical_Condition
ORDER BY admissions DESC
LIMIT 20;

-- Insurance provider analysis
SELECT
  Insurance_Provider,
  COUNT(*) AS admissions,
  SUM(Billing_Amount) AS revenue,
  AVG(Billing_Amount) AS avg_billing
FROM healthcare
GROUP BY Insurance_Provider
ORDER BY revenue DESC;

-- Top expensive stays (highest billing)
SELECT Name, Age, Gender, Medical_Condition, Hospital, Insurance_Provider, Billing_Amount, Date_of_Admission, Discharge_Date
FROM healthcare
ORDER BY Billing_Amount DESC
LIMIT 20;