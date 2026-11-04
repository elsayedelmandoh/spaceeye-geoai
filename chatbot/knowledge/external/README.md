---
title: External Knowledge Source Guide
source_url: "urn:spaceeye:external-knowledge-guide"
retrieval_date: 2026-11-03
---

# External knowledge sources

This directory holds outside reference documents added by the team lead. The
chatbot indexes every Markdown file below this directory, including this local
format guide.

Each source document must begin with a YAML front-matter block:

```yaml
---
title: Document title
source_url: https://example.org/path/to/source
retrieval_date: YYYY-MM-DD
---
```

- `title` is the public document title.
- `source_url` is the canonical public URL for the source.
- `retrieval_date` is the ISO date (`YYYY-MM-DD`) on which the team retrieved it.
- The Markdown body follows the closing `---` line and may use ordinary headings
  and paragraphs.

Record each accepted source in `chatbot/knowledge/SOURCES.csv`, whose columns are
`title,url,retrieved,kind,notes`. Keep source bodies factual and suitable for
public distribution; do not add credentials, private material, compound names,
or developer names.
