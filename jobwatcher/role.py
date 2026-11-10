"""The title rule that marks a posting as 'in my role' (finance / analytics analyst roles)."""
import re

# Role: financial analyst and close relatives (FP&A, data/BI analyst, credit, treasury, pricing...).
# A title is in role when it matches ANALYST_RE and FIELD_RE, or matches FPA_RE on its own.
ANALYST_RE = re.compile(r"\banalyst\b|\banalytics\b", re.I)
FIELD_RE = re.compile(
    r"financ|accounting|treasury|credit|investment|revenue|pricing|"
    r"business intelligence|\bbi\b|\bdata\b|strategy|strategic|risk|"
    r"supply chain|planning|reporting|forecast",
    re.I,
)
FPA_RE = re.compile(r"fp\s*&\s*a|fp\s*and\s*a|financial planning", re.I)
# Titles that look like a match but are a different job (engineers, scientists, sales).
EXCLUDE_RE = re.compile(r"engineer|scientist|developer|designer|sales|recruit", re.I)


def in_role(title: str) -> bool:
    title = title or ""
    if EXCLUDE_RE.search(title):
        return False
    if FPA_RE.search(title):
        return True
    return bool(ANALYST_RE.search(title) and FIELD_RE.search(title))
