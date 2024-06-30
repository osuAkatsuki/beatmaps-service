import math

from app.adapters.osu_mirrors.backends import AbstractBeatmapMirror
from app.adapters.osu_mirrors.selectors import AbstractMirrorSelector
from app.repositories import beatmap_mirror_requests
from app.repositories.beatmap_mirror_requests import MirrorResource


class DynamicWeightedRoundRobinMirrorSelector(AbstractMirrorSelector):
    def __init__(
        self,
        mirrors: list[AbstractBeatmapMirror],
        resource: MirrorResource,
    ) -> None:
        self.mirrors = mirrors
        self.resource = resource
        self.index = -1
        self.current_weight = 0
        self.max_weight = max(mirror.weight for mirror in mirrors)
        self.gcd_weight = self._calculate_gcd(
            [mirror.weight for mirror in mirrors],
        )

    @staticmethod
    def _calculate_gcd(weights: list[int]) -> int:
        gcd = weights[0]
        for weight in weights[1:]:
            gcd = math.gcd(gcd, weight)
        return gcd

    async def update_all_mirror_and_selector_weights(self) -> None:
        for beatmap_mirror in self.mirrors:
            beatmap_mirror.weight = await beatmap_mirror_requests.get_mirror_weight(
                beatmap_mirror.name,
                self.resource,
            )

        self.max_weight = max(mirror.weight for mirror in self.mirrors)
        self.gcd_weight = self._calculate_gcd(
            [mirror.weight for mirror in self.mirrors],
        )

    def select_mirror(self) -> AbstractBeatmapMirror:
        while True:
            self.index = (self.index + 1) % len(self.mirrors)
            if self.index == 0:
                self.current_weight -= self.gcd_weight
                if self.current_weight <= 0:
                    self.current_weight = self.max_weight
                    if self.current_weight == 0:
                        raise RuntimeError("All mirrors have 0 weight.")

            if self.mirrors[self.index].weight >= self.current_weight:
                return self.mirrors[self.index]

    def get_num_mirrors(self) -> int:
        return len(self.mirrors)
