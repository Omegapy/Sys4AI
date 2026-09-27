from pathlib import Path
p=Path('SKILLS-depo/init-new-project/scripts/init_new_project.py')
s=p.read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new)
replace('_static_spec = importlib.util.spec_from_file_location', '_collaboration_spec = importlib.util.spec_from_file_location("_sys4ai_initializer_collaboration", Path(__file__).with_name("init_collaboration.py"))\nCOLLABORATION = importlib.util.module_from_spec(_collaboration_spec)\n_collaboration_spec.loader.exec_module(COLLABORATION)\nCOLLABORATION_MODULE = COLLABORATION.MODULE\n_static_spec = importlib.util.spec_from_file_location')
replace('def _static(name, *args, **kwargs):', 'def _collaboration(name, *args, **kwargs):\n    return getattr(COLLABORATION, name)(types.SimpleNamespace(**globals()), *args, **kwargs)\n\n\ndef _static(name, *args, **kwargs):')
replace('def module_packages(operation: dict[str, Any]) -> tuple[str, ...]:\n', 'def module_packages(operation: dict[str, Any]) -> tuple[str, ...]:\n    if isinstance(operation, dict) and operation.get("module_id") == COLLABORATION_MODULE:\n        return (COLLABORATION.ROOT,)\n')
replace('def module_frozen(operation: dict[str, Any]) -> tuple[str, ...]:\n', 'def module_frozen(operation: dict[str, Any]) -> tuple[str, ...]:\n    if isinstance(operation, dict) and operation.get("module_id") == COLLABORATION_MODULE:\n        return MODULE_FROZEN + COLLABORATION.FROZEN\n')
replace('    for index, operation in enumerate(operations):\n', '    for index, operation in enumerate(operations):\n        if isinstance(operation, dict) and operation.get("module_id") == COLLABORATION_MODULE:\n            _collaboration("validate_operation", record, destination, operation, index)\n            if operation["operation_id"] in seen:\n                raise InitializationError("duplicate collaboration module operation")\n            seen.add(operation["operation_id"])\n            continue\n')
replace('    original = (_curator("selected_source_files", depot, operation) if operation["module_id"] == CURATOR_MODULE else', '    original = (_collaboration("source_files", depot) if operation["module_id"] == COLLABORATION_MODULE else\n                _curator("selected_source_files", depot, operation) if operation["module_id"] == CURATOR_MODULE else')
replace('    operation["capabilities"] = (_curator("assess", destination, integration_required=operation.get("schema_version")==2)', '    operation["capabilities"] = (_collaboration("assess", destination, operation) if operation["module_id"] == COLLABORATION_MODULE else\n                                 _curator("assess", destination, integration_required=operation.get("schema_version")==2)')
replace('                operation, proposed = (_curator("plan", depot, destination, record, previous_raw, refresh_modules)', '                operation, proposed = (_collaboration("plan", depot, destination, record, previous_raw) if module_id == COLLABORATION_MODULE else\n                                       _curator("plan", depot, destination, record, previous_raw, refresh_modules)')
replace('                proposed = (_curator("proposed_files", destination, record["identity"], check_module_sources(depot, operation), new_curator_files=operation["new_curator_files"])', '                proposed = (_collaboration("proposed_files", check_module_sources(depot, operation), operation) if module_id == COLLABORATION_MODULE else\n                            _curator("proposed_files", destination, record["identity"], check_module_sources(depot, operation), new_curator_files=operation["new_curator_files"])')
replace('def run_initialization(\n', 'def _run_initialization_base(\n')
replace('if (adopt_module not in {None, LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE}', 'if (adopt_module not in {None, LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE, COLLABORATION_MODULE}')
replace(' or adopt_module is not None and mode != "prepare-existing"', ' or adopt_module is not None and mode != "prepare-existing" and adopt_module != COLLABORATION_MODULE')
# Default activation uses the same public guarded transaction, not a second ledger.
wrapper='''def run_initialization(**arguments) -> dict[str, Any]:
    """Preserve the base edition, then enable the selected project's collaboration."""
    destination = arguments["destination"]
    record_path = destination_file(destination, RECORD)
    # The automatic selection must also resume its exact partial module.
    if record_path.is_file() and arguments.get("adopt_module") is None and not arguments.get("refresh_module") and not arguments.get("refresh_dependency"):
        current = unique_json(file_bytes(record_path))
        pending = [op for op in current.get("module_adoptions", []) if op.get("status") != "completed"]
        if pending and pending[0].get("module_id") == COLLABORATION_MODULE:
            return _run_initialization_base(**{**arguments, "adopt_module": COLLABORATION_MODULE})
    record = _run_initialization_base(**arguments)
    if record["status"] != "completed":
        return record
    depot, _ = installed_locations()
    return run_module_adoption(depot, destination, record, file_bytes(record_path), [], module_id=COLLABORATION_MODULE)


'''
replace('def main(argv: list[str] | None = None) -> int:\n', wrapper+'def main(argv: list[str] | None = None) -> int:\n')
replace('choices=[LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE, "curator"]', 'choices=[LEARNING_MODULE, ONTOLOGY_MODULE, ADVANCED_MODULE, CURATOR_MODULE, COLLABORATION_MODULE, "curator"]')
replace('    arguments = vars(parser.parse_args(argv))\n', '    collaboration_assessment = commands.add_parser("assess-collaboration", help="Inspect complete default collaboration and supported owner without executing target code")\n    collaboration_assessment.add_argument("--destination", type=Path, required=True)\n    arguments = vars(parser.parse_args(argv))\n')
replace('        result = (_curator("assess", arguments["destination"])', '        result = (_collaboration("assess", arguments["destination"]) if arguments["mode"] == "assess-collaboration" else\n                  _curator("assess", arguments["destination"])')
p.write_text(s)
p=Path('SKILLS-depo/init-new-project/scripts/init_static_health.py');s=p.read_text()
s=s.replace('    if module == h.CURATOR_MODULE:\n', '    if module == h.COLLABORATION_MODULE:\n        return (h.COLLABORATION.ROOT, *h.COLLABORATION.GUIDANCE)\n    if module == h.CURATOR_MODULE:\n',1)
s=s.replace('        elif module == h.CURATOR_MODULE:\n', '        elif module == h.COLLABORATION_MODULE:\n            detail = h._collaboration("assess", destination, operation or next((op for op in reversed(record.get("module_adoptions", [])) if op["module_id"] == module), None))\n            available = detail["enabled"]\n        elif module == h.CURATOR_MODULE:\n',1)
p.write_text(s)
