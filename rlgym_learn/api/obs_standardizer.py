from abc import abstractmethod
from typing import Generic, List, Tuple

from rlgym.api import AgentID, ObsType


class ObsStandardizer(Generic[AgentID, ObsType]):
    @abstractmethod
    def standardize(self, obs_list: List[Tuple[AgentID, ObsType]]) -> List[ObsType]:
        """
        :param obs_list: list of tuples of agent IDs and observations parallel with returned list. Agent IDs may not be unique here.
        :return: List of standardized observations, parallel with input list.
        """
        raise NotImplementedError
