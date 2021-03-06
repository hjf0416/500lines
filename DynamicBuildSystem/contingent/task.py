from graphlib import Graph
from functools import wraps
from contextlib import contextmanager
from collections import namedtuple
import re


class Project:
    def __init__(self):
        self._task_stack = []
        self._graph = Graph()
        self._todo = set() #only tasks in _todo are out of date
        self._cache = dict() #{task: result} values from previous run
        self._cache_on = True
        self._trace = None
        
    def start_tracing(self):
        """start recording every task that is invoked by this change"""
        self._trace = []
        
    def stop_tracing(self, verbose=False):
        """stop recording task invocations, and return trace as text"""
        text = '\n'.join(
            '{}{} {}'.format(
                '. ' * depth,
                'calling' if not_available else 'returning cached',
                task)
            for (depth, not_available, task) in self._trace
            if verbose or not_available
        )
                
        self._trace = None
        return text
    
    def rebuild(self):
        """Repeatedly rebuild every out-of-date task until all are current.
        If nothing has changed recently, our to-do list will be empty,
        and this call will return immediately.  Otherwise we take the
        tasks in the current to-do list, along with every consequence
        anywhere downstream of them, and call `get()` on every single
        one to force re-computation of the tasks that are either already
        invalid or that become invalid as the first few in the list are
        recomputed.
        Unless there are cycles in the task graph, this will eventually
        return.
        """
        while self._todo:
            tasks = self._graph.recursive_consequences_of(self._todo, True)
            for task in tasks:
                task.exe()
    
    def _get_from_cache(self, task):
        """get result from cache,
        if cache is off or don't have cached value return None.
        """
        if not self._cache_on:
            return None
        if task in self._todo:
            return None
        return self._cache.get(task)
    
    def set(self, task, return_value):
        """set return_value of task to cache; and clear _todo set since
        we just invoke task """
        self._todo.discard(task)
        if (task not in self._cache) or (self._cache[task] != return_value):
            self._cache[task] = return_value
            self._todo.update(self._graph.immediate_consequences_of(task))
            
    def _add_task_to_trace(self, task, return_value):
        tup = (len(self._task_stack), return_value is None, task)
        self._trace.append(tup)
    
    def pre_process(self, function, *args):
        task = Task(function, *args);
        if self._task_stack:
            self._graph.add_edge(task, self._task_stack[-1])
            
        return_value = self._get_from_cache(task)
        
        if self._trace is not None:
            self._add_task_to_trace(task, return_value)
        
        if return_value is None:
            self._graph.clear_inputs_of(task)
            self._task_stack.append(task)
        
        return return_value
        
    def post_process(self, return_value, function, *args):
        task = Task(function, *args);
        self._task_stack.pop()
        self.set(task, return_value)

    @contextmanager
    def cache_off(self):
        """Context manager that forces tasks to really be invoked.
        Even if the project has already cached the output of a
        particular task, re-running the task inside of this context
        manager will make the project re-invoke the task::
            with project.cache_off():
                my_task()
        """
        original_value = self._cache_on
        self._cache_on = False
        try:
            yield
        finally:
            self._cache_on = original_value

class Task:
    def __init__(self, function, *args):
        self.function = function;
        self.args = args;

    def exe(self):
        return self.function(*self.args)
    
    def __eq__(self, other):
        return (self.function.__name__ == other.function.__name__) and (self.args == other.args)
    
    def __hash__(self):
        return hash((self.function.__name__, self.args))
    
    def __repr__(self):
        return '{}({})'.format(self.function.__name__,', '.join(repr(arg) for arg in self.args))
    
project = Project()
pre_process = project.pre_process
post_process = project.post_process

index = """
Table of Contents
-----------------
* `tutorial.txt`
* `api.txt`
"""

tutorial = """
Beginners Tutorial
------------------
Welcome to the tutorial!
We hope you enjoy it.
"""

api = """
API Reference
-------------
You might want to read
the `tutorial.txt` first.
"""

filesystem = {'index.txt': index,
              'tutorial.txt': tutorial,
              'api.txt': api}
LINK = '<a href="{}">{}</a>'
PAGE = '<h1>{}</h1>\n<p>\n{}\n<p>'

def read(filename):
    ret = pre_process(read, filename)
    if ret is None:
        ret = filesystem[filename]
        
        post_process(ret, read, filename)
        
    return ret

def parse(filename):
    ret = pre_process(parse, filename)
    if ret is None:
        lines = read(filename).strip().splitlines()
        title = lines[0]
        body = '\n'.join(lines[2:])
        ret = (title, body)
        
        post_process(ret, parse, filename)
    
    return ret

def title_of(filename):
    ret = pre_process(title_of, filename)
    if ret is None:
        title, body = parse(filename)
        ret = title
        
        post_process(ret, title_of, filename)
        
    return ret

def body_of(filename):
    ret = pre_process(body_of, filename)
    if ret is None:
        title, body = parse(filename)
        ret = body
        
        post_process(ret, body_of, filename)
        
    return ret

def make_link(match):
    filename = match.group(1)
    print filename, title_of(filename)
    return LINK.format(filename, title_of(filename))

def render(filename):
    ret = pre_process(render, filename)
    if ret is None:
        title, body = parse(filename)
        body = re.sub(r'`([^`]+)`', make_link, body)
        ret = PAGE.format(title, body)
        
        post_process(ret, render, filename)
        
    return ret

for filename in 'index.txt', 'tutorial.txt', 'api.txt':
    render(filename);