-- Q1: Top Inventors (who has the most patents?)
SELECT i.name, COUNT(r.patent_id) AS total_patents
FROM relationships r
JOIN inventors i ON r.inventor_id = i.inventor_id
GROUP BY r.inventor_id
ORDER BY total_patents DESC
LIMIT 10;

-- Q2: Top Companies (which companies own the most patents?)
SELECT c.name, COUNT(r.patent_id) AS total_patents
FROM relationships r
JOIN companies c ON r.company_id = c.company_id
GROUP BY r.company_id
ORDER BY total_patents DESC
LIMIT 10;

-- Q3: Countries (which countries produce the most patents?)
SELECT i.country, COUNT(DISTINCT r.patent_id) AS total_patents
FROM relationships r
JOIN inventors i ON r.inventor_id = i.inventor_id
WHERE i.country IS NOT NULL AND i.country != ''
GROUP BY i.country
ORDER BY total_patents DESC
LIMIT 10;

-- Q4: Trends Over Time (patents per year)
SELECT year, COUNT(*) AS total_patents
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year ASC;

-- Q5: JOIN Query (patents with inventors and companies)
SELECT
    p.patent_id,
    p.title,
    p.filing_date,
    i.name  AS inventor_name,
    i.country,
    c.name  AS company_name
FROM patents p
JOIN relationships r ON p.patent_id  = r.patent_id
JOIN inventors     i ON r.inventor_id = i.inventor_id
JOIN companies     c ON r.company_id  = c.company_id
LIMIT 20;

-- Q6: CTE Query (top inventors with their most frequent company)
WITH inventor_patent_counts AS (
    SELECT inventor_id, COUNT(patent_id) AS total_patents
    FROM relationships
    GROUP BY inventor_id
),
inventor_top_company AS (
    SELECT
        inventor_id,
        company_id,
        COUNT(*) AS collab_count,
        RANK() OVER (PARTITION BY inventor_id ORDER BY COUNT(*) DESC) AS co_rank
    FROM relationships
    GROUP BY inventor_id, company_id
)
SELECT
    i.name            AS inventor_name,
    ipc.total_patents,
    c.name            AS top_company
FROM inventor_patent_counts ipc
JOIN inventors            i   ON ipc.inventor_id  = i.inventor_id
JOIN inventor_top_company itc ON itc.inventor_id  = ipc.inventor_id AND itc.co_rank = 1
JOIN companies            c   ON itc.company_id   = c.company_id
ORDER BY ipc.total_patents DESC
LIMIT 10;

-- Q7: Ranking Query (rank inventors using window functions)
SELECT
    inventor_name,
    total_patents,
    RANK()       OVER (ORDER BY total_patents DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY total_patents DESC) AS dense_rank,
    NTILE(4)     OVER (ORDER BY total_patents DESC) AS quartile
FROM (
    SELECT i.name AS inventor_name, COUNT(r.patent_id) AS total_patents
    FROM relationships r
    JOIN inventors i ON r.inventor_id = i.inventor_id
    GROUP BY r.inventor_id
)
ORDER BY total_patents DESC
LIMIT 20;