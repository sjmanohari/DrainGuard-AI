
from numbers import Real

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


def calculate_drainage_risk(rainfall_mm, severity, issue_type, report_age_hours):
    if isinstance(rainfall_mm, bool) or not isinstance(rainfall_mm, Real):
        raise ValueError("Rainfall must be a number")
    if rainfall_mm < 0 or rainfall_mm > 1000:
        raise ValueError("Rainfall must be between 0 and 1000 mm")

    if isinstance(report_age_hours, bool) or not isinstance(report_age_hours, Real):
        raise ValueError("Report age must be a number")
    if report_age_hours < 0 or report_age_hours > 8760:
        raise ValueError("Report age must be between 0 and 8760 hours")

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
        f"Rainfall contribution: {rainfall_points} points.",
        f"Issue contribution: {issue_points} points.",
        f"Severity contribution: {severity_points} points.",
        f"Report age contribution: {age_points} points."
    ]

    return {
        "risk_score": score,
        "risk_category": category,
        "recommended_action": action,
        "explanation": reasons,
        "model_type": "rule_based_baseline",
        "note": "Prototype risk score, not a measured flood probability."
    }


if __name__ == "__main__":
    result = calculate_drainage_risk(
        rainfall_mm=35,
        severity="high",
        issue_type="blocked_drain",
        report_age_hours=3
    )
    print(result)
