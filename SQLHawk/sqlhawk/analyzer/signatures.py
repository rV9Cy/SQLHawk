"""
Database error-message signatures.

When a SQL query breaks because of injected input, many databases leak
a distinctive error string in the response. Matching those strings lets
us guess (a) that an injection point exists and (b) which database
engine is behind it, which changes which payloads/exploits apply later.
"""

DB_SIGNATURES: dict[str, list[str]] = {
    "MySQL": [
        "you have an error in your sql syntax",
        "warning: mysql",
        "mysqli_",
        "mysql_fetch",
        "unknown column",
        "mariadb server",
    ],
    "PostgreSQL": [
        "postgresql query failed",
        "pg_query()",
        "pg::syntaxerror",
        "unterminated quoted string",
        "syntax error at or near",
    ],
    "MSSQL": [
        "unclosed quotation mark",
        "microsoft sql native client",
        "sqlserver jdbc driver",
        "system.data.sqlclient",
        "incorrect syntax near",
    ],
    "Oracle": [
        "ora-00933",
        "ora-01756",
        "ora-00921",
        "oracle error",
        "quoted string not properly terminated",
    ],
    "SQLite": [
        "sqlite3::syntaxerror",
        "sqlite_error",
        "unrecognized token",
        "near \"",
    ],
}


def identify_database(response_text: str) -> str | None:
    """Return the best-guess DB engine name based on error text, or None."""
    lowered = response_text.lower()
    for engine, needles in DB_SIGNATURES.items():
        for needle in needles:
            if needle in lowered:
                return engine
    return None
