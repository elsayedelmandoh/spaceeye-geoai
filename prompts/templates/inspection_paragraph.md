# Inspection paragraph template

## Attached facts

```json
{{facts_json}}
```

## Display context

- Compound code: `{{code}}`
- Quarter: `{{quarter}}`
- Priority level in Arabic: `{{level_word}}`
- Code-prepared Arabic reason: `{{reason_ar}}`

Treat the attached facts JSON as the only evidence source. Use the display context only when its values occur in that JSON; otherwise write `unknown` rather than infer or fill a value.

Draft exactly one Arabic paragraph for the inspection committee. Explain what the facts show, the relevant priority level, and the recommended inspection focus without making an unsupported causal claim. Do not output a preamble, heading, question, or any name. Every number, date, and code must be copied verbatim from the attached facts JSON.
