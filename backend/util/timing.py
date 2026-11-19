import time


class StepTimer:
    def __init__(self, clock=time.perf_counter):
        self._clock = clock
        self._started = self._last = clock()
        self.steps = {}

    def lap(self, name):
        now = self._clock()
        self.steps[name] = self.steps.get(name, 0.0) + (now - self._last)
        self._last = now

    def as_dict(self):
        result = {name: round(seconds, 4) for name, seconds in self.steps.items()}
        result["total"] = round(self._clock() - self._started, 4)
        return result
