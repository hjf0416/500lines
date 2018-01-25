from graphlib import Graph
from functools import wraps
import re


class Project:
    def __init__(self):
        self._task_stack = []
        self._graph = Graph()
    
    def task(self, function):
        @wraps(function)
        def wrapper(*args):
            task = Task(function, *args)
            if self._task_stack:
                self._graph.add_edge(task, self._task_stack[-1])
            self._graph.clear_inputs_of(task)
            self._task_stack.append(task)
            
            try:
                value = task.exe()
            finally:
                self._task_stack.pop()
                
            return value
        return wrapper

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
task = project.task

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


@task
def read(filename):
    return filesystem[filename]

@task
def parse(filename):
    lines = read(filename).strip().splitlines()
    title = lines[0]
    body = '\n'.join(lines[2:])
    return title, body

@task
def title_of(filename):
    title, body = parse(filename)
    return title

@task
def body_of(filename):
    title, body = parse(filename)
    return body

def make_link(match):
    filename = match.group(1)
    print filename, title_of(filename)
    return LINK.format(filename, title_of(filename))

@task
def render(filename):
    title, body = parse(filename)
    body = re.sub(r'`([^`]+)`', make_link, body)
    return PAGE.format(title,body)

for filename in 'index.txt', 'tutorial.txt', 'api.txt':
    print(render(filename))
    print('=' * 30)
    
project._graph.edges()
task = Task(read, ('index.txt'))
print project._graph.recursive_consequences_of([task])