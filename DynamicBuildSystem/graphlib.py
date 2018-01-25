from collections import defaultdict
from pprint import pprint

class Graph:
    sort_key = None
    
    def __init__(self):
        self._inputs_of = defaultdict(set)
        self._consequences_of = defaultdict(set)
        
    def add_edge(self, input_task, consequence_task):
        self._inputs_of[consequence_task].add(input_task)
        self._consequences_of[input_task].add(consequence_task)

    def edges(self):
        return [(a,b) for a in self.sorted(self._consequences_of)
                      for b in self.sorted(self._consequences_of[a])]
    
    def sorted(self, nodes, reverse=False):
        nodes = list(nodes)
        try:
            nodes.sort(key=self.sort_key, reverse=reverse)
        except TypeError:
            pass
        return nodes
    
    def immediate_consequences_of(self, task):
        return self.sorted(self._consequences_of[task])
    
    def clear_inputs_of(self, task):
        """Remove all edges leading to `task` from its previous inputs."""
        input_tasks = self._inputs_of.pop(task, ())
        for input in input_tasks:
            self._consequences_of[input].remove(task)
        
    def recursive_consequences_of(self, tasks):
        """Get recursive consequences of tasks"""
        def visit(result, tasks):
            for task in tasks:
                result.add(task)
                visit(result, self.immediate_consequences_of(task))
        
        result = set()
        visit(result, tasks)
        for task in tasks:
            result.remove(task)
        return result

g = Graph()
g.add_edge('index.rst', 'index.html')
g.add_edge('api.rst', 'api.html')
g.add_edge('tutorial.rst', 'tutorial.html')

g.add_edge('api.rst', 'api-title')
g.add_edge('api-title', 'index.html')
g.add_edge('tutorial.rst', 'tutorial-title')
g.add_edge('tutorial-title', 'index.html')
