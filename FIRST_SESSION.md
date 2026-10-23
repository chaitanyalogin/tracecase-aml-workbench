# Your first AML investigation

Goal: explain whether the alert has been resolved and what evidence supports your next step. You are acting as a trainee analyst, not declaring whether someone committed a crime.

## 1. Let the application prepare the facts

Select C001 (Anita Rao). Open Customer & evidence, then Transaction analysis. The system calculates the review-period amounts and lists the supporting transaction IDs. You do not need to recalculate every row manually. Check important totals and dates against the supplied records.

## 2. Use AI

In AI assistance, download the case prompt and paste it into ChatGPT. Ask for JSON only. Paste the returned JSON into TraceCase and click Validate and load response. If you have separate API access, the optional live AI configuration performs this step inside the app.

You can also start with `exercises/C001_ai_prompt.txt` before launching the app.

## 3. Challenge the brief

Ask these questions:

- Does each factual statement match its cited record?
- Does the draft mistake the customer's statement for corroborated fact?
- Does it claim screening was completed when the record says it was not?
- Does it turn a high income multiple into proof of crime?
- Does it explain what information would resolve the uncertainty?

Open the cited evidence beside each AI fact. Mark a claim reviewed only after checking it. An invented evidence ID will be rejected; a misleading interpretation of a real record still needs your judgment.

## 4. Record your decision

Choose close, request information or escalate for internal review. Explain at least:

1. What triggered concern.
2. What evidence supports or contradicts it.
3. What could legitimately explain the activity.
4. What is still unknown and what you would do next.

Select the relevant evidence, complete the checks and save. If using the AI brief, acknowledge each factual claim first. You can disagree with the recommendation.

## 5. Compare and repeat

Open coaching after saving, then investigate C002 (Vikram Shah). Notice how the evidence changes your conclusion even though the temporal movement ratio remains similar. A closure of an alert does not permanently clear all future activity.

## Bring back this result

Export the investigation history and share it for feedback. We can evaluate your reasoning and improve the case workflow using that concrete record.

## Terms you need today

- KYC: who the customer is and what activity is expected.
- Source of funds: the origin of the particular money being reviewed.
- Corroboration: additional evidence that supports an explanation.
- Alert: a signal to investigate, not a conclusion.
- Escalation: handing unresolved concern to the appropriate internal reviewer.

All fixtures and verification assertions in this exercise are fictional.
