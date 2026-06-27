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
