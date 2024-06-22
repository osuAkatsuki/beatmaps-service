import math
from typing import Any

from app.adapters.beatmap_mirrors import BeatmapMirror
from app.repositories import beatmap_mirror_requests


class DynamicWeightedRoundRobin:
    def __init__(
        self,
        mirrors: list[BeatmapMirror],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.mirrors = mirrors
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
            )
            print(
                "Beatmap mirror",
                beatmap_mirror.name,
                "has weight",
                beatmap_mirror.weight,
            )

        self.max_weight = max(mirror.weight for mirror in self.mirrors)
        self.gcd_weight = self._calculate_gcd(
            [mirror.weight for mirror in self.mirrors],
        )

    def select_mirror(self) -> BeatmapMirror:
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
