# DOCX Brief Guidelines

Use this reference when turning extracted `.docx` structure into summaries, action items, risks, or edit suggestions.

## Boundaries

- Read local `.docx` files supplied or approved by the user.
- Treat extraction as structural, not visual. XML parsing does not prove final rendered layout.
- Keep quoted document text concise in final responses.
- Do not invent action items, owners, due dates, or risks that are not supported by the extracted document.

## Brief Fields

- `summary`: concise overview from title, headings, early paragraphs, and repeated themes.
- `action_items`: tasks with optional owner and due date when the source states them.
- `suggested_edits`: practical improvements such as missing owner, vague deadline, long paragraph, unclear decision, or missing risk mitigation.
- `risks_or_questions`: open issues, blockers, unresolved questions, assumptions, and decisions needed.
- `source_metadata`: file name, size, counts, extraction method, and warnings.

## Extraction Cues

Action-item indicators:

- `Action:`
- `Owner:`
- `Due:`
- `Next step`
- `TODO`
- imperative verbs in meeting-note lists

Risk or question indicators:

- question marks
- `risk`
- `blocker`
- `issue`
- `dependency`
- `unknown`
- `assumption`
- `decision needed`

## Suggested Edits

Recommend edits when:

- a document has no clear heading;
- a paragraph is too long for a brief;
- an action item lacks owner or due date;
- a risk has no mitigation or next step;
- a table has empty cells or unclear column labels.

## Limitations

The bundled script is deterministic and rule-based. For complex executive briefs, legal review, tone adjustment, or nuanced writing, use Codex to synthesize from the script output and preserve source traceability.
