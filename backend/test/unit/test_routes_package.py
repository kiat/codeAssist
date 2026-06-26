import importlib
import types


def test_routes_package_keeps_assignment_submodule_addressable():
    routes = importlib.import_module("routes")
    assignment_module = importlib.import_module("routes.assignment")

    assert isinstance(routes.assignment, types.ModuleType)
    assert routes.assignment is assignment_module
    assert hasattr(routes.assignment, "db")
