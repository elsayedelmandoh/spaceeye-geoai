# Visit questions template

## Attached facts

```json
{{facts_json}}
```

## Display context

- Compound code: `{{code}}`
- Quarter: `{{quarter}}`

Treat the attached facts JSON as the only evidence source. Use the display context only when its values occur in that JSON; otherwise write `unknown` rather than infer or fill a value.

Draft exactly three Arabic questions for the inspection visit. The questions must be neutral, focused on facts that can be checked on site or against records, and free of unsupported causal claims. Do not answer the questions or output a preamble, heading, paragraph, or any name. Every number, date, and code must be copied verbatim from the attached facts JSON.
