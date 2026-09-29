from google.cloud import bigquery

PROJECT_ID = "driver-safety-system-290fe"


def get_client():
    return bigquery.Client(project=PROJECT_ID)


def get_driver_risk():
    client = get_client()

    query = """
    SELECT
      driver_id,
      COUNT(*) AS incident_count,
      ROUND(AVG(drowsiness_score),2) AS avg_score,
      CASE
        WHEN AVG(drowsiness_score) >= 0.8 THEN 'HIGH'
        WHEN AVG(drowsiness_score) >= 0.5 THEN 'MEDIUM'
        ELSE 'LOW'
      END AS risk_level
    FROM `driver-safety-system-290fe.driver_analytics.incidents_raw`
    GROUP BY driver_id
    ORDER BY avg_score DESC
    """

    results = client.query(query).result()

    return [dict(row.items()) for row in results]


def get_drowsiness_by_hour():
    client = get_client()

    query = """
    SELECT
      EXTRACT(HOUR FROM created_at) AS hour,
      COUNT(*) AS total_incidents,
      ROUND(AVG(drowsiness_score),2) AS avg_score
    FROM `driver-safety-system-290fe.driver_analytics.incidents_raw`
    GROUP BY hour
    ORDER BY hour
    """

    results = client.query(query).result()

    return [dict(row.items()) for row in results]