import importlib
import types


def test_routes_package_keeps_assignment_submodule_addressable():
    routes = importlib.import_module("routes")
    assignment_module = importlib.import_module("routes.assignment")
    ai_feedback_module = importlib.import_module("routes.ai_feedback")

    assert isinstance(routes.assignment, types.ModuleType)
    assert isinstance(routes.ai_feedback, types.ModuleType)
    assert routes.assignment is assignment_module
    assert routes.ai_feedback is ai_feedback_module
    assert hasattr(routes.assignment, "db")
    assert hasattr(routes.ai_feedback, "db")
