
# ==============================
# INFERENCE ENGINE
# ==============================

def match_condition(condition, facts):
    """
    Check whether all conditions in a rule
    match the available facts.
    """

    conditions = condition.lower().split(" and ")

    for item in conditions:

        if "=" not in item:
            return False

        fact_name, expected_value = item.split("=", 1)

        fact_name = fact_name.strip()
        expected_value = expected_value.strip()

        matched = False

        for fact in facts:

            stored_name = fact["fact_name"].strip().lower()
            stored_value = fact["fact_value"].strip().lower()

            if (stored_name == fact_name and
                    stored_value == expected_value):

                matched = True
                break

        if not matched:
            return False

    return True


def run_inference(rules, facts):
    """
    Match knowledge-base rules against input facts.
    """

    matched_rules = []

    for rule in rules:

        if match_condition(rule["condition"], facts):

            matched_rules.append({
                "rule_id": rule["id"],
                "rule_name": rule["rule_name"],
                "condition": rule["condition"],
                "conclusion": rule["conclusion"],
                "priority": rule["priority"],
                "reliability": rule["reliability"]
            })

    return matched_rules
