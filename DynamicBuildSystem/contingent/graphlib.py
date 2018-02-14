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
        
    def toplogical_sort(self, tasks):   
        indegree = defaultdict(int);
        result = []
        def dfs(node):
            result.append(node)
            indegree[node] -= 1
            for nextnode in self.immediate_consequences_of(node):
                indegree[nextnode] = indegree[nextnode] - 1
                if indegree[nextnode] == 0:
                    dfs(nextnode)
        
        for x in tasks:
            indegree[x] = 0
        
        for task in tasks:
            outs = self.immediate_consequences_of(task)
            for out in outs:
                indegree[out] = indegree[out] + 1
           
        for k, v in indegree.iteritems():
            if v == 0:
                dfs(k)
            
        return result
    
    def recursive_consequences_of(self, tasks, include = False):
        """Get recursive consequences of tasks"""
        def visit(result, tasks):
            for task in tasks:
                if result.count(task) == 0:
                    result.append(task)
                    visit(result, self.immediate_consequences_of(task))
        
        result = list()
        visit(result, tasks)
        if (include == False):
            for task in tasks:
                result.remove(task)
            
        return self.toplogical_sort(result)
