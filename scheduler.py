from kivy.clock import Clock
from time import time

class SchedulerEngine:
    def __init__(self, db, sender_callable):
        self.db = db
        self.sender = sender_callable
        self._event = None

    def start(self):
        if self._event is None:
            self._event = Clock.schedule_interval(self._tick, 1.0)

    def stop(self):
        if self._event is not None:
            self._event.cancel()
            self._event = None

    def _tick(self, *args):
        now = int(time())
        items = self.db.list_schedules()
        for row in items:
            sched_id, food_name, hopper_idx, grams, when_ts, executed, food_id = row
            if executed:
                continue
            if when_ts <= now <= when_ts + 30:
                ok = self.sender(food_id, food_name, hopper_idx, grams)
                if ok:
                    self.db.mark_executed(sched_id)
