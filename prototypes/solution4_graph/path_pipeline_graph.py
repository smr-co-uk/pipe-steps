"""Graph-based pipeline with DAG structure and topological execution."""

from collections import defaultdict, deque
from dataclasses import dataclass

from .path_item_graph import PathItem
from .path_step_graph import PathStep


@dataclass
class Connection:
    """Represents a connection between two steps."""

    from_step: str
    to_step: str
    from_channel: str
    to_channel: str

    def __repr__(self) -> str:
        return f"{self.from_step}[{self.from_channel}] -> {self.to_step}[{self.to_channel}]"


class PathPipeline:
    """Pipeline that executes steps in a DAG structure with topological ordering."""

    def __init__(self, debug: bool = False) -> None:
        """
        Initialize an empty graph pipeline.

        Args:
            debug: If True, print detailed execution information
        """
        self.steps: dict[str, PathStep] = {}
        self.graph: dict[str, list[str]] = defaultdict(list)  # step_id -> [dependent_step_ids]
        self.connections: list[Connection] = []
        self.debug = debug

    def add_step(self, step_id: str, step: PathStep) -> None:
        """
        Add a step to the pipeline.

        Args:
            step_id: Unique identifier for this step
            step: PathStep instance

        Raises:
            ValueError: If step_id already exists
        """
        if step_id in self.steps:
            raise ValueError(f"Step {step_id} already exists")

        self.steps[step_id] = step
        self.graph[step_id] = []  # Initialize adjacency list

    def connect(
        self, from_step: str, to_step: str, from_channel: str, to_channel: str
    ) -> None:
        """
        Connect an output channel of one step to an input channel of another.

        Args:
            from_step: Source step ID
            to_step: Destination step ID
            from_channel: Output channel name from source step
            to_channel: Input channel name for destination step

        Raises:
            ValueError: If steps don't exist or channels don't match declarations
        """
        # Validate steps exist
        if from_step not in self.steps:
            raise ValueError(f"Step {from_step} not found")
        if to_step not in self.steps:
            raise ValueError(f"Step {to_step} not found")

        # Validate channels
        from_step_obj = self.steps[from_step]
        to_step_obj = self.steps[to_step]

        if from_channel not in from_step_obj.get_output_channels():
            raise ValueError(
                f"Step {from_step} does not have output channel '{from_channel}'. "
                f"Available: {from_step_obj.get_output_channels()}"
            )

        if to_channel not in to_step_obj.get_input_channels():
            raise ValueError(
                f"Step {to_step} does not have input channel '{to_channel}'. "
                f"Available: {to_step_obj.get_input_channels()}"
            )

        # Add edge to graph
        self.graph[from_step].append(to_step)

        # Store connection
        conn = Connection(from_step, to_step, from_channel, to_channel)
        self.connections.append(conn)

        if self.debug:
            print(f"Connected: {conn}")

    def _topological_sort(self) -> list[str]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            List of step IDs in execution order

        Raises:
            ValueError: If graph contains cycles
        """
        # Calculate in-degree for each node
        in_degree: dict[str, int] = {step_id: 0 for step_id in self.steps}

        for step_id in self.graph:
            for neighbor in self.graph[step_id]:
                in_degree[neighbor] += 1

        # Find all nodes with in-degree 0 (starting nodes)
        queue: deque[str] = deque([step_id for step_id, degree in in_degree.items() if degree == 0])

        result: list[str] = []

        while queue:
            # Remove node from queue
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree for neighbors
            for neighbor in self.graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed
        if len(result) != len(self.steps):
            # Graph has a cycle
            unprocessed = [step_id for step_id in self.steps if step_id not in result]
            raise ValueError(f"Pipeline contains a cycle. Unprocessed steps: {unprocessed}")

        return result

    def _has_cycle(self) -> bool:
        """
        Check if the graph contains a cycle using DFS.

        Returns:
            True if cycle exists, False otherwise
        """
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for step_id in self.steps:
            if step_id not in visited:
                if dfs(step_id):
                    return True

        return False

    def _get_step_inputs(
        self, step_id: str, step_outputs: dict[str, dict[str, dict[str, PathItem]]]
    ) -> dict[str, dict[str, PathItem]]:
        """
        Gather inputs for a step from connected predecessor steps.

        Args:
            step_id: Step to gather inputs for
            step_outputs: Dictionary of outputs from all executed steps

        Returns:
            Dictionary mapping input channel names to PathItem dictionaries
        """
        inputs: dict[str, dict[str, PathItem]] = {}

        # Find all connections that feed into this step
        for conn in self.connections:
            if conn.to_step == step_id:
                # Get output from predecessor step
                if conn.from_step in step_outputs:
                    pred_outputs = step_outputs[conn.from_step]
                    if conn.from_channel in pred_outputs:
                        # Map from predecessor's output channel to this step's input channel
                        inputs[conn.to_channel] = pred_outputs[conn.from_channel]

        return inputs

    def run(self, initial_items: dict[str, PathItem], start_step: str | None = None) -> dict[str, dict[str, dict[str, PathItem]]]:
        """
        Execute the pipeline in topological order.

        Args:
            initial_items: Initial items to feed to the starting step(s)
            start_step: Optional step ID to start from (if None, uses steps with no predecessors)

        Returns:
            Dictionary mapping step IDs to their output channels and items
            Structure: {step_id: {channel_name: {item_name: PathItem}}}

        Raises:
            ValueError: If pipeline contains cycles or validation fails
        """
        # Validate pipeline structure
        if self._has_cycle():
            raise ValueError("Pipeline contains a cycle")

        # Get execution order
        execution_order = self._topological_sort()

        if self.debug:
            print("\n" + "=" * 70)
            print("EXECUTION ORDER")
            print("=" * 70)
            for i, step_id in enumerate(execution_order, 1):
                print(f"{i}. {step_id} ({self.steps[step_id].name})")

        # Track outputs from each step
        step_outputs: dict[str, dict[str, dict[str, PathItem]]] = {}

        # Execute steps in order
        for step_id in execution_order:
            step = self.steps[step_id]

            # Get inputs for this step
            if step_id == execution_order[0] and start_step is None:
                # First step gets initial items
                # Map to the step's input channels
                input_channels = step.get_input_channels()
                if len(input_channels) == 1:
                    inputs = {input_channels[0]: initial_items}
                else:
                    raise ValueError(
                        f"First step {step_id} has multiple input channels. "
                        "Please specify explicit connections."
                    )
            else:
                # Gather inputs from connected predecessors
                inputs = self._get_step_inputs(step_id, step_outputs)

            # Skip step if it has no inputs (not connected or predecessor produced no outputs)
            if not inputs:
                if self.debug:
                    print(f"\n▶ {step_id}: No inputs, skipping")
                continue

            # Execute step
            if self.debug:
                print(f"\n▶ {step_id} ({step.name})")
                for channel, items in inputs.items():
                    print(f"  Input[{channel}]: {len(items)} items")

            outputs = step.process(inputs)

            if self.debug:
                for channel, items in outputs.items():
                    print(f"  Output[{channel}]: {len(items)} items")

            # Store outputs
            step_outputs[step_id] = outputs

        return step_outputs

    def visualize(self) -> None:
        """Print a visualization of the pipeline structure."""
        print("\n" + "=" * 70)
        print("PIPELINE STRUCTURE")
        print("=" * 70)

        print("\nSteps:")
        for step_id, step in self.steps.items():
            print(f"\n  {step_id}: {step.name}")
            print(f"    Inputs:  {step.get_input_channels()}")
            print(f"    Outputs: {step.get_output_channels()}")

        print("\nConnections:")
        for conn in self.connections:
            print(f"  {conn}")

        print("\nExecution Order:")
        try:
            order = self._topological_sort()
            for i, step_id in enumerate(order, 1):
                print(f"  {i}. {step_id}")
        except ValueError as e:
            print(f"  Error: {e}")

        print("\n" + "=" * 70)

    def validate(self) -> list[str]:
        """
        Validate the pipeline configuration.

        Returns:
            List of error/warning messages
        """
        errors = []

        # Check for cycles
        if self._has_cycle():
            errors.append("Pipeline contains a cycle")

        # Check for disconnected steps
        execution_order = self._topological_sort() if not self._has_cycle() else []
        starting_steps = [
            step_id
            for step_id in self.steps
            if not any(conn.to_step == step_id for conn in self.connections)
        ]

        if len(starting_steps) == 0 and len(self.steps) > 0:
            errors.append("No starting steps found (all steps have incoming connections)")
        elif len(starting_steps) > 1:
            errors.append(f"Multiple starting steps found: {starting_steps}")

        # Check that all input channels are connected
        for step_id, step in self.steps.items():
            if step_id not in starting_steps:  # Starting steps can have unconnected inputs
                for input_channel in step.get_input_channels():
                    connected = any(
                        conn.to_step == step_id and conn.to_channel == input_channel
                        for conn in self.connections
                    )
                    if not connected:
                        errors.append(
                            f"Step {step_id}: Input channel '{input_channel}' is not connected"
                        )

        # Check for unused output channels (warning, not error)
        for step_id, step in self.steps.items():
            for output_channel in step.get_output_channels():
                connected = any(
                    conn.from_step == step_id and conn.from_channel == output_channel
                    for conn in self.connections
                )
                if not connected:
                    # Check if this is the last step in execution order
                    if execution_order and step_id == execution_order[-1]:
                        continue  # Last step's outputs don't need to be connected
                    errors.append(
                        f"Warning: Step {step_id}: Output channel '{output_channel}' is not connected"
                    )

        return errors
