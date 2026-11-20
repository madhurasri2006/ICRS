
from flask import Flask, render_template, request, redirect, url_for, flash

from database.db import create_tables, get_connection

from engine.inference import run_inference
from engine.conflict_detection import detect_conflicts
from engine.conflict_resolution import resolve_conflict


app = Flask(__name__)
app.secret_key = "icrs_secret_key"


# Create database tables
create_tables()


# ==============================
# DASHBOARD
# ==============================

@app.route('/')
def home():

    connection = get_connection()
    cursor = connection.cursor()

    # Total number of rules
    cursor.execute("SELECT COUNT(*) FROM rules")
    total_rules = cursor.fetchone()[0]

    # Retrieve rules and facts
    cursor.execute("SELECT * FROM rules")
    rules = cursor.fetchall()

    cursor.execute("SELECT * FROM facts")
    facts = cursor.fetchall()

    # Total decisions made
    cursor.execute("SELECT COUNT(*) FROM decision_history")
    decisions_made = cursor.fetchone()[0]

    connection.close()

    # Find activated rules
    matched_rules = run_inference(rules, facts)
    activated_rules = len(matched_rules)

    # Check current conflicts
    conflict = detect_conflicts(matched_rules)

    conflicts_detected = (
        1 if conflict["has_conflict"] else 0
    )

    return render_template(
        'index.html',
        total_rules=total_rules,
        activated_rules=activated_rules,
        conflicts_detected=conflicts_detected,
        decisions_made=decisions_made
    )


# ==============================
# KNOWLEDGE BASE MANAGEMENT
# ==============================

# Display Knowledge Base
@app.route('/rules')
def rules():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM rules")
    all_rules = cursor.fetchall()

    connection.close()

    return render_template(
        'rules.html',
        rules=all_rules
    )


# Add a new rule
@app.route('/add_rule', methods=['POST'])
def add_rule():

    rule_name = request.form.get(
        'rule_name', ''
    ).strip()

    condition = request.form.get(
        'condition', ''
    ).strip()

    conclusion = request.form.get(
        'conclusion', ''
    ).strip()

    try:

        priority = int(
            request.form.get('priority')
        )

        reliability = float(
            request.form.get('reliability')
        )

        if not 1 <= priority <= 10:
            raise ValueError

        if not 0 <= reliability <= 1:
            raise ValueError

        if not rule_name or not condition or not conclusion:
            raise ValueError

    except (ValueError, TypeError):

        flash("Please enter valid rule details.")

        return redirect(url_for('rules'))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO rules
        (rule_name, condition, conclusion, priority, reliability)
        VALUES (?, ?, ?, ?, ?)
    """, (
        rule_name,
        condition,
        conclusion,
        priority,
        reliability
    ))

    connection.commit()
    connection.close()

    flash("Rule added successfully!")

    return redirect(url_for('rules'))


# Delete a rule
@app.route('/delete_rule/<int:rule_id>', methods=['POST'])
def delete_rule(rule_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM rules WHERE id = ?",
        (rule_id,)
    )

    connection.commit()
    connection.close()

    flash("Rule deleted successfully!")

    return redirect(url_for('rules'))


# ==============================
# INPUT FACTS MANAGEMENT
# ==============================

# Display Input Facts
@app.route('/facts')
def facts():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM facts ORDER BY id DESC"
    )

    all_facts = cursor.fetchall()

    connection.close()

    return render_template(
        'facts.html',
        facts=all_facts
    )


# Add a new fact
@app.route('/add_fact', methods=['POST'])
def add_fact():

    fact_name = request.form.get(
        'fact_name', ''
    ).strip()

    fact_value = request.form.get(
        'fact_value', ''
    ).strip()

    if not fact_name or not fact_value:

        flash("Please enter valid fact details.")

        return redirect(url_for('facts'))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO facts (fact_name, fact_value)
        VALUES (?, ?)
    """, (
        fact_name,
        fact_value
    ))

    connection.commit()
    connection.close()

    flash("Fact added successfully!")

    return redirect(url_for('facts'))


# Delete a fact
@app.route('/delete_fact/<int:fact_id>', methods=['POST'])
def delete_fact(fact_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM facts WHERE id = ?",
        (fact_id,)
    )

    connection.commit()
    connection.close()

    flash("Fact deleted successfully!")

    return redirect(url_for('facts'))


# ==============================
# DECISION ANALYSIS
# ==============================

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():

    connection = get_connection()
    cursor = connection.cursor()

    # Retrieve stored rules
    cursor.execute("SELECT * FROM rules")
    rules = cursor.fetchall()

    # Retrieve stored facts
    cursor.execute("SELECT * FROM facts")
    facts = cursor.fetchall()

    connection.close()

    # Step 1: Run inference engine
    matched_rules = run_inference(
        rules,
        facts
    )

    # Step 2: Check whether any rules matched
    if not matched_rules:

        return render_template(
            'analysis.html',
            matched_rules=[],
            conflict=None,
            resolution=None,
            selected_conclusion=None
        )

    # Step 3: Detect conflicts
    conflict = detect_conflicts(
        matched_rules
    )

    resolution = None
    selected_conclusion = None
    selected_rule_name = None
    resolution_method = "No conflict"

    # Step 4: Resolve conflicts
    if conflict["has_conflict"]:

        resolution = resolve_conflict(
            conflict["conflicting_rules"]
        )

        if resolution["resolved"]:

            selected_conclusion = (
                resolution["selected_conclusion"]
            )

            selected_rule_name = (
                resolution["selected_rule"]["rule_name"]
            )

            resolution_method = resolution["reason"]

    else:

        # All matching rules have the same conclusion
        selected_rule = matched_rules[0]

        selected_conclusion = (
            selected_rule["conclusion"]
        )

        selected_rule_name = (
            selected_rule["rule_name"]
        )

    # Step 5: Save history only when POST is submitted
    if request.method == 'POST' and selected_conclusion:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO decision_history
            (
                selected_conclusion,
                selected_rule,
                resolution_method,
                explanation
            )
            VALUES (?, ?, ?, ?)
        """, (
            selected_conclusion,
            selected_rule_name,
            resolution_method,
            "Analysis completed successfully."
        ))

        connection.commit()
        connection.close()

        # Redirect to prevent duplicate submissions
        return redirect(url_for('analyze'))

    # Step 6: Display analysis results
    return render_template(
        'analysis.html',
        matched_rules=matched_rules,
        conflict=conflict,
        resolution=resolution,
        selected_conclusion=selected_conclusion
    )


# ==============================
# DECISION HISTORY
# ==============================

@app.route('/history')
def history():

    connection = get_connection()
    cursor = connection.cursor()

    # Retrieve previous decisions
    cursor.execute("""
        SELECT * FROM decision_history
        ORDER BY id DESC
    """)

    decisions = cursor.fetchall()

    connection.close()

    return render_template(
        'history.html',
        decisions=decisions
    )


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == '__main__':

    app.run(debug=True)
