import ast
from pathlib import Path


def _read_revision_id(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "revision" in names and isinstance(node.value, ast.Constant):
                return node.value.value
    return None


def _literal_assignment(path, variable_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if variable_name in names:
                return ast.literal_eval(node.value)
    return None


def test_migration_revision_ids_are_unique():
    versions_dir = Path(__file__).parents[2] / "migrations" / "versions"
    revisions = {}

    for migration_path in versions_dir.glob("*.py"):
        revision = _read_revision_id(migration_path)
        if revision is None:
            continue

        revisions.setdefault(revision, []).append(migration_path.name)

    duplicates = {
        revision: filenames
        for revision, filenames in revisions.items()
        if len(filenames) > 1
    }

    assert duplicates == {}


def test_migration_graph_has_single_head():
    versions_dir = Path(__file__).parents[2] / "migrations" / "versions"
    revisions = set()
    referenced_revisions = set()

    for migration_path in versions_dir.glob("*.py"):
        revision = _literal_assignment(migration_path, "revision")
        down_revision = _literal_assignment(migration_path, "down_revision")
        if revision is None:
            continue

        revisions.add(revision)
        if isinstance(down_revision, tuple):
            referenced_revisions.update(
                revision_id for revision_id in down_revision if revision_id
            )
        elif down_revision:
            referenced_revisions.add(down_revision)

    heads = revisions - referenced_revisions

    assert len(heads) == 1, f"Expected one Alembic head, found: {sorted(heads)}"
