from typing import List, Set
from datetime import datetime
from app.schemas.pipeline_state import PipelineState, ValidationIssue, RepairLogEntry


class RefinementEngine:
    """
    Stage 4 of the pipeline: cross-layer consistency checks and automatic fixes.

    This stage is deterministic (no LLM calls) by design — cross-referencing fields
    across already-generated schemas is a mechanical task, and doing it in code
    instead of via another prompt keeps it fast, cheap, and fully reproducible.
    """

    def refine(self, state: PipelineState) -> PipelineState:
        if not all([state.architecture, state.ui, state.api, state.db, state.auth, state.business_logic]):
            state.validation_issues.append(
                ValidationIssue(
                    layer="cross_layer",
                    severity="error",
                    message="Cannot refine: one or more schemas are missing.",
                )
            )
            state.status = "failed"
            return state

        entity_names = {e.name.lower() for e in state.architecture.entities}
        role_names = {r.name.lower() for r in state.architecture.roles}

        # 1. Auto-repairs & Normalizations first
        self._fix_role_name_typos(state, role_names)
        self._fix_db_column_types_and_fields(state)
        self._check_auth_protected_routes_cover_api(state)

        # 2. Validation & Consistency checks (reconcile remaining errors/warnings)
        self._check_api_maps_to_known_entity(state, entity_names)
        self._check_ui_api_bindings_exist(state)
        self._check_db_tables_match_entities(state, entity_names)
        self._check_db_foreign_key_integrity(state)
        self._check_api_db_field_consistency(state)

        state.status = "refined"
        return state

    def _check_api_maps_to_known_entity(self, state: PipelineState, entity_names: Set[str]):
        """Flags API endpoints that reference an entity not present in the architecture."""
        for endpoint in state.api.endpoints:
            if endpoint.maps_to_entity and endpoint.maps_to_entity.lower() not in entity_names:
                state.validation_issues.append(
                    ValidationIssue(
                        layer="cross_layer",
                        severity="error",
                        message=(
                            f"API endpoint {endpoint.method} {endpoint.path} maps to "
                            f"unknown entity '{endpoint.maps_to_entity}' (hallucinated field)."
                        ),
                        field_path=f"api.endpoints[{endpoint.path}].maps_to_entity",
                    )
                )

    def _check_ui_api_bindings_exist(self, state: PipelineState):
        """
        Flags UI components whose api_binding doesn't match any real API endpoint path.
        This is the classic 'UI fields must map to API' consistency check from the spec.
        """
        known_paths = {e.path for e in state.api.endpoints}
        # Also accept binding to a path prefix (e.g. "/api/contacts" binds fine even
        # if the exact endpoint is "/api/contacts/{id}") — check prefix match too.
        for page in state.ui.pages:
            for component in page.components:
                if not component.api_binding:
                    continue
                exact_match = component.api_binding in known_paths
                prefix_match = any(
                    p.startswith(component.api_binding) or component.api_binding.startswith(p.split("{")[0].rstrip("/"))
                    for p in known_paths
                )
                if not exact_match and not prefix_match:
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="cross_layer",
                            severity="warning",
                            message=(
                                f"UI component '{component.name}' on page '{page.name}' binds to "
                                f"'{component.api_binding}', which doesn't match any API endpoint."
                            ),
                            field_path=f"ui.pages[{page.name}].components[{component.name}].api_binding",
                        )
                    )

    def _check_db_tables_match_entities(self, state: PipelineState, entity_names: Set[str]):
        """Flags DB tables that don't correspond to any known entity (hallucinated table)."""
        table_names_normalized = {t.name.lower().rstrip("s") for t in state.db.tables}
        for entity in entity_names:
            entity_singular = entity.rstrip("s")
            if entity_singular not in table_names_normalized and entity not in table_names_normalized:
                state.validation_issues.append(
                    ValidationIssue(
                        layer="cross_layer",
                        severity="error",
                        message=f"Entity '{entity}' from architecture has no corresponding DB table.",
                        field_path="db.tables",
                    )
                )

    def _fix_role_name_typos(self, state: PipelineState, role_names: Set[str]):
        """
        Auto-repairs case mismatches in role names (e.g. architecture has 'Admin' but
        auth/API/UI schemas generated 'admin' or 'ADMIN').
        This is a safe, deterministic fix and does not count against LLM repair budgets.
        """
        canonical_roles = {r.lower(): r for r in role_names}

        # 1. Fix auth.roles names
        for role_def in state.auth.roles:
            normalized = role_def.name.lower()
            if normalized in canonical_roles and role_def.name != canonical_roles[normalized]:
                old_name = role_def.name
                role_def.name = canonical_roles[normalized]
                state.repair_log.append(
                    self._make_repair_entry(
                        layer="auth",
                        issue=f"Role name case mismatch: '{old_name}' vs architecture canonical '{role_def.name}'",
                        action="repaired",
                    )
                )

        # 2. Fix ui.pages access_roles
        for page in state.ui.pages:
            new_access_roles = []
            for role in page.access_roles:
                normalized = role.lower()
                if normalized in ("any", "public"):
                    new_access_roles.append(role)
                elif normalized in canonical_roles:
                    if role != canonical_roles[normalized]:
                        state.repair_log.append(
                            self._make_repair_entry(
                                layer="ui",
                                issue=f"Page '{page.name}' access role case mismatch: '{role}' -> canonical '{canonical_roles[normalized]}'",
                                action="repaired",
                            )
                        )
                    new_access_roles.append(canonical_roles[normalized])
                else:
                    new_access_roles.append(role)
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="ui",
                            severity="warning",
                            message=f"Page '{page.name}' references unknown role '{role}'",
                            field_path=f"ui.pages[{page.name}].access_roles",
                        )
                    )
            page.access_roles = new_access_roles

        # 3. Fix api.endpoints allowed_roles
        for endpoint in state.api.endpoints:
            new_allowed_roles = []
            for role in endpoint.allowed_roles:
                normalized = role.lower()
                if normalized in ("any", "public"):
                    new_allowed_roles.append(role)
                elif normalized in canonical_roles:
                    if role != canonical_roles[normalized]:
                        state.repair_log.append(
                            self._make_repair_entry(
                                layer="api",
                                issue=f"Endpoint '{endpoint.method} {endpoint.path}' allowed role case mismatch: '{role}' -> canonical '{canonical_roles[normalized]}'",
                                action="repaired",
                            )
                        )
                    new_allowed_roles.append(canonical_roles[normalized])
                else:
                    new_allowed_roles.append(role)
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="api",
                            severity="warning",
                            message=f"Endpoint '{endpoint.method} {endpoint.path}' references unknown role '{role}'",
                            field_path=f"api.endpoints[{endpoint.path}].allowed_roles",
                        )
                    )
            endpoint.allowed_roles = new_allowed_roles

        # 4. Fix business_logic.rules applies_to_role
        for rule in state.business_logic.rules:
            normalized = rule.applies_to_role.lower()
            if normalized in ("any", "public"):
                pass
            elif normalized in canonical_roles:
                if rule.applies_to_role != canonical_roles[normalized]:
                    old_role = rule.applies_to_role
                    rule.applies_to_role = canonical_roles[normalized]
                    state.repair_log.append(
                        self._make_repair_entry(
                            layer="business_logic",
                            issue=f"Business rule '{rule.name}' applies_to_role case mismatch: '{old_role}' -> canonical '{rule.applies_to_role}'",
                            action="repaired",
                        )
                    )
            else:
                state.validation_issues.append(
                    ValidationIssue(
                        layer="business_logic",
                        severity="warning",
                        message=f"Business rule '{rule.name}' references unknown role '{rule.applies_to_role}'",
                        field_path=f"business_logic.rules[{rule.name}].applies_to_role",
                    )
                )

    def _check_auth_protected_routes_cover_api(self, state: PipelineState):
        """Flags or auto-protects API endpoints requiring auth that aren't listed in auth.protected_routes."""
        protected = set(state.auth.protected_routes)
        for endpoint in state.api.endpoints:
            if not endpoint.auth_required:
                continue

            base_path = endpoint.path.split("{")[0].rstrip("/")
            if not base_path:
                continue

            # Check if this base_path is covered by any path prefix in protected_routes
            covered = False
            for p in protected:
                p_clean = p.rstrip("/")
                if base_path == p_clean or base_path.startswith(p_clean + "/") or p_clean.startswith(base_path + "/"):
                    covered = True
                    break

            if not covered:
                state.auth.protected_routes.append(base_path)
                protected.add(base_path)
                state.repair_log.append(
                    self._make_repair_entry(
                        layer="auth",
                        issue=f"Endpoint {endpoint.method} {endpoint.path} requires auth but wasn't in protected_routes.",
                        action="repaired",
                    )
                )

    def _fix_db_column_types_and_fields(self, state: PipelineState):
        """
        Auto-repairs DB column types, casing mismatches, and missing columns
        based on the system design layer entities.
        """
        sql_type_map = {
            "string": "TEXT",
            "integer": "INTEGER",
            "float": "REAL",
            "boolean": "BOOLEAN",
            "date": "DATETIME",
            "datetime": "DATETIME",
            "enum": "TEXT",
            "reference": "INTEGER"
        }

        def pluralize(name: str) -> str:
            name_lower = name.lower()
            if name_lower.endswith("y"):
                return name_lower[:-1] + "ies"
            elif name_lower.endswith("s"):
                return name_lower
            else:
                return name_lower + "s"

        entity_by_table = {}
        for entity in state.architecture.entities:
            plural = pluralize(entity.name)
            entity_by_table[plural] = entity

        from app.schemas.db_schema import Column

        for table in state.db.tables:
            entity = entity_by_table.get(table.name.lower())
            if not entity:
                continue

            # Map of lower(field_name) -> canonical EntityField
            entity_fields = {f.name.lower(): f for f in entity.fields}
            existing_col_names = set()

            # 1. Correct existing columns
            for col in table.columns:
                existing_col_names.add(col.name.lower())
                field = entity_fields.get(col.name.lower())

                if field:
                    # Fix name casing
                    if col.name != field.name:
                        old_name = col.name
                        col.name = field.name
                        state.repair_log.append(
                            self._make_repair_entry(
                                layer="db",
                                issue=f"DB column casing mismatch in table '{table.name}': '{old_name}' -> canonical '{field.name}'",
                                action="repaired"
                            )
                        )
                    
                    # Fix column type
                    expected_type = sql_type_map.get(field.type, "TEXT")
                    if col.type != expected_type:
                        old_type = col.type
                        col.type = expected_type
                        state.repair_log.append(
                            self._make_repair_entry(
                                layer="db",
                                issue=f"DB column type mismatch in table '{table.name}.{col.name}': '{old_type}' -> canonical '{expected_type}'",
                                action="repaired"
                            )
                        )
                    
                    # Fix nullable
                    expected_nullable = not field.required
                    if col.nullable != expected_nullable and not col.primary_key:
                        col.nullable = expected_nullable
                        state.repair_log.append(
                            self._make_repair_entry(
                                layer="db",
                                issue=f"DB column nullable mismatch in table '{table.name}.{col.name}': expected {expected_nullable}",
                                action="repaired"
                            )
                        )

            # 2. Add missing columns from entity fields
            for field in entity.fields:
                if field.name.lower() not in existing_col_names:
                    new_col = Column(
                        name=field.name,
                        type=sql_type_map.get(field.type, "TEXT"),
                        primary_key=(field.name.lower() == "id"),
                        nullable=not field.required
                    )
                    table.columns.append(new_col)
                    state.repair_log.append(
                        self._make_repair_entry(
                            layer="db",
                            issue=f"Missing DB column '{field.name}' in table '{table.name}' added based on architecture entity.",
                            action="repaired"
                        )
                    )

            # 3. Add relation columns (foreign keys)
            for rel in entity.relations:
                if rel.relation_type in ("many_to_one", "one_to_one"):
                    via_field_lower = rel.via_field.lower()
                    if via_field_lower not in {c.name.lower() for c in table.columns}:
                        target_table = pluralize(rel.target_entity)
                        new_col = Column(
                            name=rel.via_field,
                            type="INTEGER",
                            primary_key=False,
                            foreign_key=f"{target_table}.id",
                            nullable=True
                        )
                        table.columns.append(new_col)
                        state.repair_log.append(
                            self._make_repair_entry(
                                layer="db",
                                issue=f"Missing FK column '{rel.via_field}' (pointing to '{target_table}.id') added to table '{table.name}'",
                                action="repaired"
                            )
                        )

    def _check_db_foreign_key_integrity(self, state: PipelineState):
        """Validates that all foreign key references point to existing tables and columns."""
        if not state.db:
            return

        table_names = {t.name.lower(): t for t in state.db.tables}

        for table in state.db.tables:
            for col in table.columns:
                if not col.foreign_key:
                    continue

                parts = col.foreign_key.split(".")
                if len(parts) != 2:
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="db",
                            severity="error",
                            message=f"Invalid foreign key format '{col.foreign_key}' on column '{table.name}.{col.name}'. Expected 'table.column'.",
                            field_path=f"db.tables[{table.name}].columns[{col.name}].foreign_key"
                        )
                    )
                    continue

                target_table_name, target_col_name = parts[0].lower(), parts[1].lower()
                target_table = table_names.get(target_table_name)

                if not target_table:
                    # Singular/plural auto-repair helper
                    repaired = False
                    for possible_name, possible_table in table_names.items():
                        if (possible_name == target_table_name + "s") or (target_table_name == possible_name + "s") or (possible_name == target_table_name + "es"):
                            old_fk = col.foreign_key
                            col.foreign_key = f"{possible_table.name}.{parts[1]}"
                            target_table = possible_table
                            repaired = True
                            state.repair_log.append(
                                self._make_repair_entry(
                                    layer="db",
                                    issue=f"Fixed FK table name mismatch: '{old_fk}' -> '{col.foreign_key}'",
                                    action="repaired"
                                )
                            )
                            break

                    if not repaired:
                        state.validation_issues.append(
                            ValidationIssue(
                                layer="db",
                                severity="error",
                                message=f"Foreign key '{col.foreign_key}' on column '{table.name}.{col.name}' points to non-existent table '{parts[0]}'.",
                                field_path=f"db.tables[{table.name}].columns[{col.name}].foreign_key"
                            )
                        )
                        continue

                # Check target column
                target_cols = {c.name.lower() for c in target_table.columns}
                if target_col_name not in target_cols:
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="db",
                            severity="error",
                            message=f"Foreign key '{col.foreign_key}' on column '{table.name}.{col.name}' points to non-existent column '{parts[1]}' in table '{target_table.name}'.",
                            field_path=f"db.tables[{table.name}].columns[{col.name}].foreign_key"
                        )
                    )

    def _check_api_db_field_consistency(self, state: PipelineState):
        """
        Checks for mismatches between API request/response fields and DB table columns.
        Flags warnings if required DB columns are missing from POST requests or if
        API requests/responses reference non-existent DB columns.
        """
        if not state.api or not state.db:
            return

        def pluralize(name: str) -> str:
            name_lower = name.lower()
            if name_lower.endswith("y"):
                return name_lower[:-1] + "ies"
            elif name_lower.endswith("s"):
                return name_lower
            else:
                return name_lower + "s"

        table_by_name = {t.name.lower(): t for t in state.db.tables}

        for endpoint in state.api.endpoints:
            if not endpoint.maps_to_entity:
                continue

            target_table_name = pluralize(endpoint.maps_to_entity)
            table = table_by_name.get(target_table_name)
            if not table:
                continue

            db_cols = {c.name.lower(): c for c in table.columns}

            # Check request/response fields exist in DB
            for field in endpoint.request_fields:
                if field.lower() not in db_cols:
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="cross_layer",
                            severity="warning",
                            message=f"API endpoint '{endpoint.method} {endpoint.path}' requests field '{field}', which does not exist in DB table '{table.name}'.",
                            field_path=f"api.endpoints[{endpoint.path}].request_fields"
                        )
                    )

            for field in endpoint.response_fields:
                if field.lower() not in db_cols:
                    state.validation_issues.append(
                        ValidationIssue(
                            layer="cross_layer",
                            severity="warning",
                            message=f"API endpoint '{endpoint.method} {endpoint.path}' returns field '{field}', which does not exist in DB table '{table.name}'.",
                            field_path=f"api.endpoints[{endpoint.path}].response_fields"
                        )
                    )

            # For POST (creation) endpoints, check if all required DB columns are in request_fields
            if endpoint.method == "POST":
                api_req_fields_lower = {f.lower() for f in endpoint.request_fields}
                for col in table.columns:
                    if col.primary_key or col.foreign_key:
                        continue
                    if not col.nullable and col.name.lower() not in api_req_fields_lower:
                        state.validation_issues.append(
                            ValidationIssue(
                                layer="cross_layer",
                                severity="warning",
                                message=f"POST endpoint '{endpoint.method} {endpoint.path}' is missing required DB column '{col.name}' from request_fields.",
                                field_path=f"api.endpoints[{endpoint.path}].request_fields"
                            )
                        )

    @staticmethod
    def _make_repair_entry(layer: str, issue: str, action: str) -> RepairLogEntry:
        return RepairLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            layer=layer,
            issue=issue,
            action=action,
            attempt=1,
        )


refinement_engine = RefinementEngine()