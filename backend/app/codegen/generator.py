"""
Stage 6 – Code Generation Engine
=================================
Converts a fully validated ``PipelineState`` into a runnable Node.js/Express
application.  The generated project lives under
``<GENERATED_APPS_DIR>/<request_id>/`` and can be started with:

    npm install && node server.js

The engine uses Jinja2 templates (stored in ``templates/``) so that each part
of the scaffolded app can be independently modified without touching Python.

Type-mapping table (DBSchema column types → SQLite affinity):
    string   → TEXT
    integer  → INTEGER
    float    → REAL
    boolean  → INTEGER (0/1)
    date     → TEXT
    datetime → TEXT
    enum     → TEXT
    reference→ INTEGER (FK)
"""

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings
from app.schemas.pipeline_state import PipelineState
from app.schemas.db_schema import DBSchema, Table, Column

# ── Jinja2 Environment ────────────────────────────────────────────────────────
_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape([]),   # JS/JSON – no HTML escaping
    keep_trailing_newline=True,
)

# Add tojson filter for JS templates
_env.filters["tojson"] = lambda v: json.dumps(v)


# ── SQL type mapping ─────────────────────────────────────────────────────────
_SQL_TYPES: Dict[str, str] = {
    "string": "TEXT",
    "integer": "INTEGER",
    "float": "REAL",
    "boolean": "INTEGER",
    "date": "TEXT",
    "datetime": "TEXT",
    "enum": "TEXT",
    "reference": "INTEGER",
}


def _to_sql_type(col_type: str) -> str:
    return _SQL_TYPES.get(col_type.lower(), "TEXT")


# ── Column DTO for the db.js template ────────────────────────────────────────
class _ColDTO:
    def __init__(self, col: Column, is_pk: bool = False):
        self.name = col.name
        self.sql_type = _to_sql_type(col.type)
        self.primary_key = is_pk
        self.not_null = col.required
        self.default = None  # extend later if needed


# ── Table DTO for the db.js template ─────────────────────────────────────────
class _TableDTO:
    def __init__(self, table: Table):
        self.name = table.name
        # The first column named "id" becomes the PK; everything else is normal
        self.columns: List[_ColDTO] = [
            _ColDTO(col, is_pk=(col.name == "id")) for col in table.columns
        ]


# ── Main engine ───────────────────────────────────────────────────────────────
class CodegenEngine:
    """Generate a Node.js + Express + SQLite project from a PipelineState."""

    def generate(self, state: PipelineState) -> Path:
        """
        Scaffold the Node.js project and return the project root directory.

        Args:
            state: A PipelineState with ``status == 'validated'`` (or 'repaired').

        Returns:
            Path to the generated project root.

        Raises:
            RuntimeError: if required schemas (db, auth) are missing.
        """
        if state.db is None:
            raise RuntimeError("Cannot codegen: DB schema is missing from PipelineState.")

        app_name = (
            state.intent.app_name if state.intent else "generated-app"
        )
        project_dir = settings.GENERATED_APPS_DIR / state.request_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Ensure `routes/` and `middleware/` sub-directories exist
        (project_dir / "routes").mkdir(exist_ok=True)
        (project_dir / "middleware").mkdir(exist_ok=True)

        # Context shared across all templates
        entities = state.architecture.entities if state.architecture else []
        entity_names = [e.name for e in entities]

        # -- package.json --
        self._render(
            "package.json.j2",
            project_dir / "package.json",
            app_name=app_name,
        )

        # -- .env --
        (project_dir / ".env").write_text(
            "PORT=3000\n"
            "JWT_SECRET=change-me-in-production\n",
            encoding="utf-8",
        )

        # -- db.js --
        table_dtos = [_TableDTO(t) for t in state.db.tables]

        # Always ensure there's a `users` table for auth
        user_table_names = [t.name.lower() for t in state.db.tables]
        if "users" not in user_table_names:
            table_dtos.append(self._synthetic_users_table())

        self._render(
            "db.js.j2",
            project_dir / "db.js",
            tables=table_dtos,
        )

        # -- server.js --
        self._render(
            "server.js.j2",
            project_dir / "server.js",
            app_name=app_name,
            entities=entities,
        )

        # -- middleware/auth.js --
        self._render(
            "middleware/auth.js.j2",
            project_dir / "middleware" / "auth.js",
        )

        # -- routes/auth.js --
        self._render(
            "routes/auth.js.j2",
            project_dir / "routes" / "auth.js",
        )

        # -- routes/<entity>.js for each entity --
        for table in state.db.tables:
            # Build list of column names (excluding id)
            non_pk_cols = [c.name for c in table.columns if c.name != "id"]
            self._render(
                "routes/entity.js.j2",
                project_dir / "routes" / f"{table.name.lower()}.js",
                entity_name=table.name,
                columns=non_pk_cols,
            )

        # Update state
        state.generated_app_path = str(project_dir)
        state.status = "complete"

        return project_dir

    def zip_project(self, project_dir: Path) -> Path:
        """Create a .zip of the generated project and return its path."""
        zip_path = project_dir.parent / f"{project_dir.name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in project_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(project_dir.parent))
        return zip_path

    # ── helpers ────────────────────────────────────────────────────────────────
    def _render(self, template_name: str, dest: Path, **ctx: Any) -> None:
        """Render a Jinja2 template and write it to *dest*."""
        tpl = _env.get_template(template_name)
        dest.write_text(tpl.render(**ctx), encoding="utf-8")

    @staticmethod
    def _synthetic_users_table() -> _TableDTO:
        """Return a minimal users table DTO when none was generated."""
        cols_raw = [
            ("id", "integer", True),
            ("email", "string", True),
            ("password_hash", "string", True),
            ("role", "string", True),
            ("created_at", "datetime", False),
        ]
        dto = _TableDTO.__new__(_TableDTO)
        dto.name = "users"
        dto.columns = []
        for name, typ, required in cols_raw:
            col_dto = _ColDTO.__new__(_ColDTO)
            col_dto.name = name
            col_dto.sql_type = _to_sql_type(typ)
            col_dto.primary_key = name == "id"
            col_dto.not_null = required
            col_dto.default = None
            dto.columns.append(col_dto)
        return dto


codegen_engine = CodegenEngine()
