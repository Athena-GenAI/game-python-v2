"""
Agent module for the GAME SDK.

This module provides the core Agent and supporting classes for creating and managing
GAME agents. It handles agent state management, worker coordination, and session tracking.

Key Components:
- Session: Manages agent session state
- WorkerConfig: Configures worker behavior and action space
- Agent: Main agent class that coordinates workers and handles state

Example:
    # Create a simple agent
    agent = Agent(
        api_key="your_api_key",
        name="My Agent",
        agent_description="A helpful agent",
        agent_goal="To assist users",
        get_agent_state_fn=lambda x, y: {"status": "ready"}
    )
"""

from typing import List, Optional, Callable, Dict, Any
import uuid
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.utils import create_agent, create_workers, post
from game_sdk.game.exceptions import ValidationError


class Session:
    """Manages agent session state.

    A Session represents a single interaction context with an agent.
    It maintains session-specific data like IDs and function results.

    Attributes:
        id (str): Unique session identifier
        function_result (Optional[FunctionResult]): Result of the last executed function

    Example:
        session = Session()
        print(f"Session ID: {session.id}")
    """

    def __init__(self):
        """Initialize a new session with a unique ID."""
        self.id = str(uuid.uuid4())
        self.function_result: Optional[FunctionResult] = None

    def reset(self):
        """Reset the session state.

        Creates a new session ID and clears any existing function results.
        """
        self.id = str(uuid.uuid4())
        self.function_result = None


class WorkerConfig:
    """Configuration for a worker instance.

    WorkerConfig defines how a worker behaves, including its action space,
    state management, and description.

    Attributes:
        id (str): Unique identifier for the worker
        worker_description (str): Description of the worker's capabilities
        instruction (str): Specific instructions for the worker
        get_state_fn (Callable): Function to get worker's current state
        action_space (Dict[str, Function]): Available actions for the worker

    Args:
        id (str): Worker identifier
        worker_description (str): Description of worker capabilities
        get_state_fn (Callable): State retrieval function
        action_space (List[Function]): List of available actions
        instruction (str, optional): Additional instructions for the worker

    Example:
        config = WorkerConfig(
            id="search_worker",
            worker_description="Searches for information",
            get_state_fn=get_state,
            action_space=[search_action],
            instruction="Search efficiently"
        )
    """

    def __init__(
        self,
        id: str,
        worker_description: str,
        get_state_fn: Callable,
        action_space: List[Function],
        instruction: Optional[str] = "",
    ):
        self.id = id
        self.worker_description = worker_description
        self.instruction = instruction
        self.get_state_fn = get_state_fn
        
        # Setup get state function with instructions
        self.get_state_fn = lambda function_result, current_state: {
            "instructions": self.instruction,
            **get_state_fn(function_result, current_state),
        }

        # Convert action space list to dictionary for easier lookup
        self.action_space: Dict[str, Function] = {
            f.get_function_def()["fn_name"]: f for f in action_space
        }


class Agent:
    """Main agent class for the GAME SDK.

    The Agent class coordinates workers and manages the overall agent state.
    It handles agent creation, worker management, and state transitions.

    Attributes:
        name (str): Agent name
        agent_goal (str): Primary goal of the agent
        agent_description (str): Description of agent capabilities
        workers (Dict[str, WorkerConfig]): Configured workers
        agent_state (dict): Current agent state
        agent_id (str): Unique identifier for the agent

    Args:
        api_key (str): API key for authentication
        name (str): Agent name
        agent_goal (str): Primary goal of the agent
        agent_description (str): Description of agent capabilities
        get_agent_state_fn (Callable): Function to get agent state
        workers (Optional[List[WorkerConfig]]): List of worker configurations

    Raises:
        ValueError: If API key is not set
        ValidationError: If state function returns invalid data
        APIError: If agent creation fails
        AuthenticationError: If API key is invalid

    Example:
        agent = Agent(
            api_key="your_api_key",
            name="Support Agent",
            agent_goal="Help users with issues",
            agent_description="A helpful support agent",
            get_agent_state_fn=get_state
        )
    """

    def __init__(
        self,
        api_key: str,
        name: str,
        agent_goal: str,
        agent_description: str,
        get_agent_state_fn: Callable,
        workers: Optional[List[WorkerConfig]] = None,
    ):
        self._base_url: str = "https://api.virtuals.io"
        self._api_key: str = api_key

        # Validate API key
        if not self._api_key:
            raise ValueError("API key not set")

        # Initialize session
        self._session = Session()

        # Set basic agent properties
        self.name = name
        self.agent_goal = agent_goal
        self.agent_description = agent_description

        # Set up workers
        if workers is not None:
            self.workers = {w.id: w for w in workers}
        else:
            self.workers = {}
        self.current_worker_id = None

        # Set up agent state function
        self.get_agent_state_fn = get_agent_state_fn

        # Validate state function
        initial_state = self.get_agent_state_fn(None, None)
        if not isinstance(initial_state, dict):
            raise ValidationError("State function must return a dictionary")

        # Initialize agent state
        self.agent_state = initial_state

        # Create agent instance
        self.agent_id = create_agent(
            self._base_url,
            self._api_key,
            self.name,
            self.agent_description,
            self.agent_goal
        )

    def compile(self):
        """Compile the agent by setting up its workers.

        This method initializes all workers and creates the necessary
        task generator configurations.

        Raises:
            ValueError: If no workers are configured
            ValidationError: If worker state functions return invalid data
            APIError: If worker creation fails

        Example:
            agent.compile()
        """
        if not self.workers:
            raise ValueError("No workers added to the agent")

        workers_list = list(self.workers.values())

        # Create workers and get map ID
        self._map_id = create_workers(
            self._base_url,
            self._api_key,
            workers_list
        )
        self.current_worker_id = next(iter(self.workers.values())).id

        # Initialize worker states
        worker_states = {}
        for worker in workers_list:
            initial_state = worker.get_state_fn(None, None)
            if not isinstance(initial_state, dict):
                raise ValidationError(f"Worker {worker.id} state function must return a dictionary")
            worker_states[worker.id] = initial_state

        self.worker_states = worker_states

        return self._map_id

    def reset(self):
        """Reset the agent session.

        Creates a new session ID and clears any existing function results.
        """
        self._session.reset()

    def add_worker(self, worker_config: WorkerConfig):
        """Add a worker to the agent's worker dictionary.

        Args:
            worker_config (WorkerConfig): Worker configuration to add

        Returns:
            Dict[str, WorkerConfig]: Updated worker dictionary
        """
        self.workers[worker_config.id] = worker_config
        return self.workers

    def get_worker_config(self, worker_id: str):
        """Get a worker configuration from the agent's worker dictionary.

        Args:
            worker_id (str): ID of the worker to retrieve

        Returns:
            WorkerConfig: Worker configuration for the given ID
        """
        return self.workers[worker_id]

    def get_worker(self, worker_id: str):
        """Get a worker instance from the agent's worker dictionary.

        Args:
            worker_id (str): ID of the worker to retrieve

        Returns:
            Worker: Worker instance for the given ID
        """
        worker_config = self.get_worker_config(worker_id)
        return Worker(
            api_key=self._api_key,
            description=self.agent_description,
            instruction=worker_config.instruction,
            get_state_fn=worker_config.get_state_fn,
            action_space=worker_config.action_space,
        )

    def _get_action(
        self,
        function_result: Optional[FunctionResult] = None
    ) -> ActionResponse:
        """Get the next action from the GAME API.

        Args:
            function_result (Optional[FunctionResult]): Result of the last executed function

        Returns:
            ActionResponse: Next action from the GAME API
        """
        # Dummy function result if None is provided
        if function_result is None:
            function_result = FunctionResult(
                action_id="",
                action_status=FunctionResultStatus.DONE,
                feedback_message="",
                info={},
            )

        # Set up payload
        data = {
            "location": self.current_worker_id,
            "map_id": self._map_id,
            "environment": self.worker_states[self.current_worker_id],
            "functions": [
                f.get_function_def()
                for f in self.workers[self.current_worker_id].action_space.values()
            ],
            "events": {},
            "agent_state": self.agent_state,
            "current_action": (
                function_result.model_dump(
                    exclude={'info'}) if function_result else None
            ),
            "version": "v2",
        }

        # Make API call
        response = post(
            base_url=self._base_url,
            api_key=self._api_key,
            endpoint=f"/v2/agents/{self.agent_id}/actions",
            data=data,
        )

        return ActionResponse.model_validate(response)

    def step(self):
        """Take a step in the agent's workflow.

        This method gets the next action from the GAME API, executes it,
        and updates the agent's state.
        """
        # Get next task/action from GAME API
        action_response = self._get_action(self._session.function_result)
        action_type = action_response.action_type

        print("#" * 50)
        print("STEP")
        print(f"Current Task: {action_response.agent_state.current_task}")
        print(f"Action response: {action_response}")
        print(f"Action type: {action_type}")

        # If new task is updated/generated
        if (
            action_response.agent_state.hlp
            and action_response.agent_state.hlp.change_indicator
        ):
            print("New task generated")
            print(f"Task: {action_response.agent_state.current_task}")

        # Execute action
        if action_type in [
            ActionType.CALL_FUNCTION,
            ActionType.CONTINUE_FUNCTION,
        ]:
            print(f"Action Selected: {action_response.action_args['fn_name']}")
            print(f"Action Args: {action_response.action_args['args']}")

            if not action_response.action_args:
                raise ValueError("No function information provided by GAME")

            self._session.function_result = (
                self.workers[self.current_worker_id]
                .action_space[action_response.action_args["fn_name"]]
                .execute(**action_response.action_args)
            )

            print(f"Function result: {self._session.function_result}")

            # Update worker states
            updated_worker_state = self.workers[self.current_worker_id].get_state_fn(
                self._session.function_result, self.worker_states[self.current_worker_id])
            self.worker_states[self.current_worker_id] = updated_worker_state

        elif action_response.action_type == ActionType.WAIT:
            print("Task ended completed or ended (not possible with current actions)")

        elif action_response.action_type == ActionType.GO_TO:
            if not action_response.action_args:
                raise ValueError("No location information provided by GAME")

            next_worker = action_response.action_args["location_id"]
            print(f"Next worker selected: {next_worker}")
            self.current_worker_id = next_worker

        else:
            raise ValueError(
                f"Unknown action type: {action_response.action_type}")

        # Update agent state
        self.agent_state = self.get_agent_state_fn(
            self._session.function_result, self.agent_state)

    def run(self):
        """Run the agent's workflow.

        This method starts the agent's workflow and continues until stopped.
        """
        self._session = Session()
        while True:
            self.step()
