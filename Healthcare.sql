SELECT COUNT(*) AS Total_Rows FROM healthcare;

SELECT * FROM healthcare LIMIT 5;

-- Total Patients
SELECT COUNT(DISTINCT Name) AS Total_Patients
FROM healthcare;

-- Total Revenue
SELECT SUM(`Billing Amount`) AS Total_Revenue
FROM healthcare;

-- Average Revenue Per Patient
SELECT AVG(`Billing Amount`) AS Avg_Revenue
FROM healthcare;

SELECT AVG(DATEDIFF(`Discharge Date`, `Date of Admission`))
AS Avg_Length_of_Stay
FROM healthcare;

-- Admission Type Distribution
SELECT `Admission Type`,
       COUNT(*) AS Patient_Count
FROM healthcare
GROUP BY `Admission Type`;

SELECT Gender,
       COUNT(*) AS Patient_Count
FROM healthcare
GROUP BY Gender;

SELECT 
    CASE 
        WHEN Age < 20 THEN 'Below 20'
        WHEN Age BETWEEN 20 AND 40 THEN '20-40'
        WHEN Age BETWEEN 41 AND 60 THEN '41-60'
        ELSE '60+'
    END AS Age_Group,
    COUNT(*) AS Patient_Count
FROM healthcare
GROUP BY Age_Group;

-- Revenue by Medical Condition

SELECT `Medical Condition`,
       SUM(`Billing Amount`) AS Revenue
FROM healthcare
GROUP BY `Medical Condition`
ORDER BY Revenue DESC;

-- Revenue by Hospital

SELECT Hospital,
       SUM(`Billing Amount`) AS Revenue
FROM healthcare
GROUP BY Hospital
ORDER BY Revenue DESC;

-- Revenue by Insurance Provider

SELECT `Insurance Provider`,
       SUM(`Billing Amount`) AS Revenue
FROM healthcare
GROUP BY `Insurance Provider`
ORDER BY Revenue DESC;

SELECT 
    DATE_FORMAT(`Date of Admission`, '%Y-%m') AS Month,
    SUM(`Billing Amount`) AS Monthly_Revenue
FROM healthcare
GROUP BY Month
ORDER BY Month;

SELECT 
    Hospital,
    SUM(`Billing Amount`) AS Total_Revenue,
    RANK() OVER (ORDER BY SUM(`Billing Amount`) DESC) AS Revenue_Rank
FROM healthcare
GROUP BY Hospital;

SELECT 
    Month,
    Monthly_Revenue,
    SUM(Monthly_Revenue) OVER (ORDER BY Month) AS Running_Total
FROM (
    SELECT 
        DATE_FORMAT(`Date of Admission`, '%Y-%m') AS Month,
        SUM(`Billing Amount`) AS Monthly_Revenue
    FROM healthcare
    GROUP BY Month
) t;

SELECT 
    `Medical Condition`,
    SUM(`Billing Amount`) AS Total_Revenue
FROM healthcare
GROUP BY `Medical Condition`
ORDER BY Total_Revenue DESC
LIMIT 5;

SELECT 
    `Medical Condition`,
    AVG(DATEDIFF(`Discharge Date`, `Date of Admission`)) AS Avg_Stay
FROM healthcare
GROUP BY `Medical Condition`
ORDER BY Avg_Stay DESC;

SELECT *
FROM healthcare
WHERE `Billing Amount` > (
    SELECT AVG(`Billing Amount`) FROM healthcare
);



