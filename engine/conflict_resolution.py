
# ==============================
# CONFLICT RESOLUTION
# ==============================

def calculate_specificity(condition):

    conditions = condition.lower().split(" and ")

    return len([
        item for item in conditions
        if item.strip()
    ])


def resolve_conflict(conflicting_rules):

    if not conflicting_rules:
        return {
            "resolved": False,
            "selected_rule": None,
            "reason": "No conflicting rules available."
        }

    # Step 1: Rank by priority, specificity and reliability
    ranked_rules = []

    for rule in conflicting_rules:

        specificity = calculate_specificity(
            rule.get("condition", "")
        )

        ranking = (
            rule["priority"],
            specificity,
            rule["reliability"]
        )

        ranked_rules.append((ranking, rule))

    # Step 2: Sort by highest ranking
    ranked_rules.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_ranking = ranked_rules[0][0]

    # Step 3: Find rules with equal ranking
    top_rules = [
        rule for ranking, rule in ranked_rules
        if ranking == best_ranking
    ]

    # Step 4: Apply recency if rankings are tied
    if len(top_rules) > 1:

        selected_rule = max(
            top_rules,
            key=lambda rule: rule["rule_id"]
        )

        reason = (
            "Priority, specificity and reliability were tied. "
            "The latest rule was selected using recency."
        )

    else:

        selected_rule = top_rules[0]

        reason = (
            "Selected using priority, specificity and reliability."
        )

    return {
        "resolved": True,
        "selected_rule": selected_rule,
        "selected_conclusion": selected_rule["conclusion"],
        "reason": reason
    }
