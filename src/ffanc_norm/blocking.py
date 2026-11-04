from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameScheduler:
    fft_length: int
    hop_length: int

    def __post_init__(self) -> None:
        if self.fft_length <= 0:
            raise ValueError("fft_length must be positive")
        if self.hop_length <= 0 or self.hop_length > self.fft_length:
            raise ValueError("invalid hop_length")

    @property
    def overlap_fraction(self) -> float:
        return 1.0 - self.hop_length / self.fft_length

    def starts(self, n_samples: int) -> list[int]:
        """Starts of complete N-sample analysis frames."""
        if n_samples < self.fft_length:
            return []
        return list(range(0, n_samples - self.fft_length + 1, self.hop_length))

    def hop_ranges(self, n_samples: int) -> list[tuple[int, int]]:
        """Full causal H-sample adaptation intervals."""
        n_hops = n_samples // self.hop_length
        return [
            (b * self.hop_length, (b + 1) * self.hop_length)
            for b in range(n_hops)
        ]
