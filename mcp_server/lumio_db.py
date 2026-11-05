"""Lumio DB: MCP server that answers questions about the Lumio TV fleet.

The database is ``mcp_server/lumio.sql`` (models, devices, firmware releases,
support tickets). On every start it is loaded into an in-memory SQLite
database opened read-only, so nothing an agent does can change it.

    python mcp_server/lumio_db.py          # started by the agent, talks MCP over stdio

Uses the official MCP SDK when it is installed, otherwise ``mcp_lite.py``
(standard library only). Nothing to install.
"""

import sqlite3
import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations
    from pydantic import Field
except ImportError:  # no SDK installed: the same API from the stdlib-only shim
    from mcp_lite import MCPServer, ToolError, ToolAnnotations, Field

SQL_FILE = Path(__file__).resolve().with_name("lumio.sql")
MAX_ROWS = 200
READ_ONLY = ToolAnnotations(readOnlyHint=True)


def open_database(sql_file=SQL_FILE):
    """A fresh in-memory copy of the database that refuses every write."""
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.executescript(Path(sql_file).read_text(encoding="utf-8"))
    db.execute("PRAGMA query_only = ON")
    return db


db = open_database()

mcp = MCPServer(
    "lumio-db",
    instructions=(
        "Baza floty telewizorów Lumio u klientów: modele, urządzenia, wydania firmware'u i zgłoszenia supportu. "
        "Najpierw wywołaj describe_database, potem odpowiadaj zapytaniami run_query. "
        "Jeśli baza nie ma danych potrzebnych do odpowiedzi, powiedz to wprost zamiast zgadywać."
    ),
)


@mcp.tool(annotations=READ_ONLY)
def describe_database():
    """Tabele bazy floty Lumio: definicja każdej tabeli z opisem kolumn i dozwolonymi wartościami oraz liczba wierszy.

    Wywołaj najpierw, zanim napiszesz zapytanie do run_query.
    """
    tables = []
    for name, definition in db.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY rowid"):
        rows = db.execute('SELECT COUNT(*) FROM "%s"' % name).fetchone()[0]
        tables.append({"table": name, "rows": rows, "definition": definition})
    return {"tables": tables}


@mcp.tool(annotations=READ_ONLY)
def run_query(
    sql: Annotated[
        str,
        Field(description="Jedno zapytanie SELECT w dialekcie SQLite, np. SELECT region, COUNT(*) FROM devices GROUP BY region"),
    ],
):
    """Wykonuje jedno zapytanie SELECT na bazie floty Lumio i zwraca nazwy kolumn oraz wiersze (najwyżej 200).

    Tylko odczyt: INSERT, UPDATE, DELETE i zmiany schematu są odrzucane. Nazwy tabel i kolumn zwraca describe_database.
    """
    statement = sql.strip().rstrip(";").strip()
    if not statement.lower().startswith(("select", "with")):
        raise ToolError("Dozwolone jest tylko jedno zapytanie SELECT (albo WITH ... SELECT). Baza jest tylko do odczytu.")
    try:
        cursor = db.execute(statement)
        rows = cursor.fetchmany(MAX_ROWS + 1)
    except (sqlite3.Error, sqlite3.Warning) as exc:
        raise ToolError("Błąd SQL: %s. Nazwy tabel i kolumn zwraca describe_database." % exc)
    columns = [column[0] for column in cursor.description]
    return {
        "columns": columns,
        "rows": [list(row) for row in rows[:MAX_ROWS]],
        "truncated": len(rows) > MAX_ROWS,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
