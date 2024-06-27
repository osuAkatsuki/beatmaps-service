from abc import ABC
from abc import abstractmethod

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror


class AbstractMirrorSelector(ABC):
    @abstractmethod
    def select_mirror(self) -> AbstractBeatmapMirror: ...

    @abstractmethod
    def get_num_mirrors(self) -> int: ...
