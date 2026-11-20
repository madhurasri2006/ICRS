
# ==============================
# CONFLICT DETECTION
# ==============================

def detect_conflicts(matched_rules):
    """
    Identify whether matched rules produce
    different conclusions.
    """

    conclusions = set()

    for rule in matched_rules:
        conclusion = rule["conclusion"].strip().lower()
        conclusions.add(conclusion)

    has_conflict = len(conclusions) > 1

    return {
        "has_conflict": has_conflict,
        "conclusions": list(conclusions),
        "conflicting_rules": matched_rules if has_conflict else []
    }
