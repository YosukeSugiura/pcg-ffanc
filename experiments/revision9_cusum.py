"""Fixed hop-level detector registered in REVISION_RULE_9."""
import math


class CUSUM:
    def __init__(self, threshold, window, hop):
        self.h, self.k, self.hop = threshold, window, hop
        self.history = []
        self.total = self.minimum = 0.0
        self.minimum_end = window - 1

    def update(self, squared_sum, count, hop_index):
        if count != self.hop or not math.isfinite(squared_sum):
            raise ValueError('invalid CUSUM residual power')
        q = math.log(max(squared_sum / count, 1e-30))
        tau = None
        if len(self.history) >= self.k:
            z = q - sum(self.history[-self.k:]) / self.k
            self.total += z
            if self.total <= self.minimum:
                self.minimum = self.total
                self.minimum_end = hop_index
            if self.total - self.minimum >= self.h:
                tau = max(0, min((self.minimum_end + 1) * self.hop, (hop_index + 1) * self.hop - 1))
                self.total = self.minimum = 0.0
                self.minimum_end = hop_index
        self.history.append(q)
        return tau
