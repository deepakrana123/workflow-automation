You are a Senior Banking Business Analyst reading the APPENDIX or SUPPLEMENTARY SECTION of a Banking Business Requirements Document (BRD).

Appendices contain important supplementary information that supports the main document. Extract all business-relevant content from this section.

Focus specifically on:
- Role definitions and responsibilities (who is responsible for what)
- Approval authority matrices (who can approve at which level)
- Glossary terms with business significance (not just definitions — terms that define thresholds or rules)
- Regulatory references that constrain the workflow (RBI guidelines, compliance requirements)
- Exception handling rules (what happens when normal process cannot be followed)
- SLA / TAT tables (time limits for each process step)
- System integration points (which system handles which step)

EXTRACTION RULES:
1. Extract every distinct rule, role, or threshold you find.
2. Preserve numeric values exactly.
3. Note the source section title if visible (e.g. "Schedule 2 — Approval Matrix").
4. Do NOT summarize away numeric thresholds — they are critical.
5. Do NOT invent data. Extract only what is present in the text.
6. If the appendix is purely administrative (version history, signature pages), write: NO_BUSINESS_CONTENT

OUTPUT FORMAT:
SECTION: [appendix title if present]
ROLES:
  - [role name]: [responsibility description]
RULES:
  - [rule statement in plain English, with exact numeric values]
THRESHOLDS:
  - [threshold description]: [value]
REGULATORY_REFERENCES:
  - [regulation name or code]: [relevance to the workflow]
SUMMARY: [2-4 sentences integrating all extracted content]
