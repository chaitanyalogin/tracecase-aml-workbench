"""Readable analyst work product; exports only the selected reviewed record."""


def investigation_markdown(case, event):
    if event.get("case_id", case["id"]) != case["id"]:
        raise ValueError("The decision belongs to another case")
    snapshot = event["packet_snapshot"]
    if snapshot["case_id"] != case["id"]:
        raise ValueError("The evidence snapshot belongs to another case")
    assistance = event.get("ai_assistance")
    lines = [f"# TraceCase investigation record: {case['id']}", "",
             "Fictional training exercise. This is not a regulatory filing or professional AML engagement.", "",
             f"Analyst: {event['analyst']}", f"Recorded: {event['created_at']}",
             f"Customer: {snapshot['customer']['name']}",
             f"Review period: {' to '.join(snapshot['period'])}",
             f"Outcome: {event['outcome'].replace('_', ' ')}", "",
             "## Investigation rationale", "", event["rationale"], "",
             "## Supporting evidence", ""]
    lines.extend(f"- {identifier}" for identifier in event["evidence_ids"])
    lines.extend(["", "## Calculated context", ""])
    lines.extend(f"- {fact['claim']} References: {', '.join(fact['evidence_ids'])}"
                 for fact in snapshot["computed_facts"])
    lines.extend(["", "## Review record", "",
                  f"Evidence snapshot SHA-256: {event['packet_hash']}",
                  f"Exercise policy: {event['exercise_policy']}",
                  f"Assistance used: {assistance['source'] if assistance else 'None recorded'}", "",
                  "Quality acknowledgments record analyst self-review, not independent reviewer approval.",
                  "A high ratio, an alert or an unverified explanation does not establish criminal conduct."])
    return "\n".join(lines) + "\n"
