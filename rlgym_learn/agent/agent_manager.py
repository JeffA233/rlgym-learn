import os
from typing import Any, Dict, Generic, Iterable, List, Optional, Tuple

import numpy as np
from rlgym.api import (
    ActionSpaceType,
    ActionType,
    AgentID,
    ObsSpaceType,
    ObsType,
    RewardType,
    StateType,
)
from rlgym_learn_backend import AgentManager as RustAgentManager
from rlgym_learn_backend import EnvAction
from torch import Tensor, as_tensor

from rlgym_learn.api import AgentController, DerivedAgentControllerConfig, StateMetrics
from rlgym_learn.experience import Timestep

from ..learning_coordinator_config import LearningCoordinatorConfigModel


class AgentManager(
    Generic[
        AgentID,
        ObsType,
        ActionType,
        RewardType,
        StateType,
        ObsSpaceType,
        ActionSpaceType,
        StateMetrics,
    ]
):
    def __init__(
        self,
        agent_controllers: Dict[
            str,
            AgentController[
                Any,
                AgentID,
                ObsType,
                ActionType,
                RewardType,
                StateType,
                ObsSpaceType,
                ActionSpaceType,
                StateMetrics,
                Any,
            ],
        ],
    ) -> None:
        self.agent_controllers = agent_controllers
        self.agent_controllers_list = list(agent_controllers.values())
        self.n_agent_controllers = len(agent_controllers)
        self.rust_agent_manager = RustAgentManager(agent_controllers)
        assert (
            self.n_agent_controllers > 0
        ), "There must be at least one agent controller!"

    def process_timestep_data(
        self,
        timestep_data: Dict[
            str,
            Tuple[
                List[Timestep],
                Optional[Tensor],
                Optional[StateMetrics],
                Optional[StateType],
            ],
        ],
    ):
        for agent_controller in self.agent_controllers_list:
            agent_controller.process_timestep_data(timestep_data)

    def get_env_actions(
        self,
        env_obs_data_dict: Dict[str, Tuple[List[AgentID], List[ObsType]]],
        state_info: Dict[
            str,
            Tuple[
                Optional[StateType],
                Optional[Dict[AgentID, bool]],
                Optional[Dict[AgentID, bool]],
            ],
        ],
    ) -> Dict[str, EnvAction]:
        """
        Function to get env actions from the agent controllers.
        :param env_obs_data_dict: Dictionary with environment ids as keys and parallel lists of Agent IDs and observations, to be used to get actions if the env action chosen is "step".
        :param state_info: Dictionary with environment ids as keys and state information as values, to be passed to agent controllers to decide the env action.
        :return: Dictionary with environment ids as keys and EnvAction instances as values
        """
        return self.rust_agent_manager.get_env_actions(env_obs_data_dict, state_info)

    def set_space_types(self, obs_space: ObsSpaceType, action_space: ActionSpaceType):
        for agent_controller in self.agent_controllers_list:
            agent_controller.set_space_types(obs_space, action_space)

    def set_device(self, device: str):
        for agent_controller in self.agent_controllers_list:
            agent_controller.set_device(device)

    def load_agent_controllers(
        self,
        learner_config: LearningCoordinatorConfigModel,
    ):
        for agent_controller_name, agent_controller in self.agent_controllers.items():
            assert (
                agent_controller_name in learner_config.agent_controllers_config
            ), f"Agent {agent_controller_name} not present in agent_controllers_config"
            agent_controller_config = agent_controller.validate_config(
                learner_config.agent_controllers_config[agent_controller_name]
            )
            agent_controller.load(
                DerivedAgentControllerConfig(
                    agent_controller_name=agent_controller_name,
                    agent_controller_config=agent_controller_config,
                    base_config=learner_config.base_config,
                    process_config=learner_config.process_config,
                    save_folder=os.path.join(
                        learner_config.agent_controllers_save_folder,
                        str(agent_controller_name),
                    ),
                )
            )

    def save_agent_controllers(self):
        for agent_controller in self.agent_controllers_list:
            agent_controller.save_checkpoint()

    def cleanup(self):
        for agent_controller in self.agent_controllers_list:
            agent_controller.cleanup()

    # TODO: what's the point of this again?
    def is_learning(self):
        return any(
            [
                agent_controller.is_learning()
                for agent_controller in self.agent_controllers_list
            ]
        )
