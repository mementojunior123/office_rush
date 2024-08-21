from utils.my_timer import Timer
from typing import Callable

class TaskScheduler:
    def __init__(self) -> None:
        self.scheduled_tasks : dict[Task, Timer] = {}
        self.continous_tasks : dict[Task, Timer] = {}

    def schedule_task(self, time : float, callback : Callable, *args, **kwargs):
        new_task = Task(callback, *args, **kwargs)
        self.scheduled_tasks[new_task] = Timer(time)
        return new_task
    
    def schedule_continuous_task(self, time : float, callback : Callable, *args, **kwargs):
        new_task = Task(callback, *args, **kwargs)
        self.continous_tasks[Task(callback, *args, **kwargs)] = Timer(time)
        return new_task
    
    def update(self):
        to_remove = []
        for task in self.scheduled_tasks:
            if self.scheduled_tasks[task].isover():
                task.execute()
                to_remove.append(task)
        
        for task in to_remove:
            self.scheduled_tasks.pop(task)

        to_remove.clear()

        for task in self.continous_tasks:
            task.execute()
            if self.continous_tasks[task].isover():
                to_remove

        for task in to_remove:
            self.continous_tasks.pop(task)


class Task:
    def __init__(self, callback : Callable, *args, **kwargs) -> None:
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
    
    def execute(self):
        self.callback(*self.args, **self.kwargs)