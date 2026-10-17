
from numbers import Real
import math
import json
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta

ISSUE_WEIGHTS = {
    "blocked_drain": 35,
    "stagnant_water": 25,
    "dumped_garbage": 20,
    "plastic_waste": 15
}

SEVERITY_WEIGHTS = {
    "low": 5,
    "medium": 15,
    "high": 25,
    "critical": 30
}


def validate_number(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(name + " must be a number")

    if not math.isfinite(value) or value < minimum or value > maximum:
        raise ValueError(
            name + " must be between " + str(minimum) +
            " and " + str(maximum)
        )


def calculate_drainage_risk(
    rainfall_mm, severity, issue_type, report_age_hours
):
    validate_number(rainfall_mm, "Rainfall", 0, 1000)
    validate_number(report_age_hours, "Report age", 0, 8760)

    if not isinstance(severity, str):
        raise ValueError("Invalid severity")

    severity = severity.strip().lower()

    if severity not in SEVERITY_WEIGHTS:
        raise ValueError("Severity must be low, medium, high, or critical")

    if not isinstance(issue_type, str):
        raise ValueError("Invalid issue type")

    issue_type = issue_type.strip().lower()

    if issue_type not in ISSUE_WEIGHTS:
        raise ValueError("Unsupported issue type")

    if rainfall_mm < 5:
        rainfall_points = 0
    elif rainfall_mm < 20:
        rainfall_points = 10
    elif rainfall_mm < 50:
        rainfall_points = 20
    else:
        rainfall_points = 30

    issue_points = ISSUE_WEIGHTS[issue_type]
    severity_points = SEVERITY_WEIGHTS[severity]

    if report_age_hours <= 6:
        age_points = 10
    elif report_age_hours <= 24:
        age_points = 5
    else:
        age_points = 0

    score = min(
        rainfall_points + issue_points + severity_points + age_points,
        100
    )

    if score >= 65:
        category = "High"
        action = "Prioritize inspection and check for possible flooding."
    elif score >= 35:
        category = "Medium"
        action = "Schedule an inspection and monitor rainfall."
    else:
        category = "Low"
        action = "Continue monitoring and verify the reported issue."

    reasons = [
        "Rainfall contribution: " + str(rainfall_points) + " points.",
        "Issue contribution: " + str(issue_points) + " points.",
        "Severity contribution: " + str(severity_points) + " points.",
        "Report age contribution: " + str(age_points) + " points."
    ]

    return {
        "risk_score": score,
        "risk_category": category,
        "recommended_action": action,
        "explanation": reasons,
        "model_type": "rule_based_baseline",
        "note": "Prototype risk score, not a measured flood probability."
    }


def fetch_rainfall_mm(latitude, longitude, fallback_mm=0):
    validate_number(latitude, "Latitude", -90, 90)
    validate_number(longitude, "Longitude", -180, 180)
    validate_number(fallback_mm, "Fallback rainfall", 0, 1000)

    try:
        params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation",
            "forecast_days": 2,
            "timezone": "GMT"
        })

        url = "https://api.open-meteo.com/v1/forecast?" + params

        with urlopen(url, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))

        times = data["hourly"]["time"]
        rainfall = data["hourly"]["precipitation"]

        now = datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )
        end_time = now + timedelta(hours=24)

        total = 0
        count = 0

        for time_value, amount in zip(times, rainfall):
            hour = datetime.fromisoformat(time_value)

            if hour.tzinfo is None:
                hour = hour.replace(tzinfo=timezone.utc)
            else:
                hour = hour.astimezone(timezone.utc)

            if now <= hour < end_time:
                if amount is not None:
                    total += float(amount)
                count += 1

        if count == 0:
            raise ValueError("Rainfall forecast unavailable")

        return round(total, 2), "Open-Meteo"

    except Exception as error:
        print("Open-Meteo unavailable:", str(error))
        return fallback_mm, "Fallback"


def assess_drainage_risk(
    latitude, longitude, severity, issue_type,
    report_age_hours, fallback_mm=0
):
    rainfall_mm, rainfall_source = fetch_rainfall_mm(
        latitude, longitude, fallback_mm
    )

    result = calculate_drainage_risk(
        rainfall_mm,
        severity,
        issue_type,
        report_age_hours
    )

    result["rainfall_mm"] = rainfall_mm
    result["rainfall_source"] = rainfall_source

    return result


if __name__ == "__main__":
    result = assess_drainage_risk(
        latitude=13.0827,
        longitude=80.2707,
        severity="high",
        issue_type="blocked_drain",
        report_age_hours=3,
        fallback_mm=10
    )

    print(result)
