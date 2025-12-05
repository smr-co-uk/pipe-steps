What I'd like to do is have branching in the path package so that PathItems get routed to a PathStep that needs that PathItem. The PathItem should need to know which PathStep it will be routed to. So for example there could be failures in the process function and we would like to send failures to a different PathStep. So the PathStep.process function has this signature.
```
def process(self, items: dict[str, PathItem]) -> dict[str, PathItem]:
```

Each PathStep picks the PathItems by name from the items dict but its hidden inside the process function. Each PathStep also returns zero or more dicts containing PathItems that is if it produced any for those names as some PathItems could product two named items one of which will be empty.
If the Pipeline knew which named items were required by a PathStep and what the outputs might be could it create a DAG either before hand.
What would a design like this look like