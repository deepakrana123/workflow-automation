from collections import defaultdict


class ExecutionPlanBuilder:
    def build(self, workflow):
        graph = defaultdict(list)
        actions = workflow["workflow"]["actions"]
        for action in actions:
            name = action["name"]
            graph[name]

            for dep in action["dependencies"]:
                graph[dep].append(name)
        return graph
