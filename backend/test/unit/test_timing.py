from util.timing import StepTimer


def _fake_clock(times):
    values = iter(times)
    return lambda: next(values)


def test_lap_records_time_since_previous_lap():
    timer = StepTimer(clock=_fake_clock([0.0, 1.0, 3.5, 4.0]))
    timer.lap("first")
    timer.lap("second")

    assert timer.as_dict() == {"first": 1.0, "second": 2.5, "total": 4.0}


def test_repeated_lap_name_accumulates():
    timer = StepTimer(clock=_fake_clock([0.0, 1.0, 2.0, 4.0, 5.0]))
    timer.lap("step")
    timer.lap("other")
    timer.lap("step")

    assert timer.as_dict() == {"step": 3.0, "other": 1.0, "total": 5.0}
