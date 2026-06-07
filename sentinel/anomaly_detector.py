import math
import time
from collections import defaultdict, deque
from typing import List, Dict, Optional

INJECTION_SIGNATURES = [
    "ignore previous instructions",
    "ignore your previous instructions",
    "disregard your guidelines",
    "you are now a",
    "pretend you are",
    "forget everything",
    "bypass your",
    "your new instructions are",
    "repeat your system prompt",
    "output your instructions",
    "what are your instructions",
    "act as if you have no",
    "dan mode",
]

class AnomalyDetector:
    def __init__(self, window_size=50, z_threshold=3.0,
                 rate_limit=20, rate_window_secs=60, min_baseline=5):
        self._tok_windows = defaultdict(lambda: deque(maxlen=window_size))
        self._ts_windows = defaultdict(lambda: deque(maxlen=rate_limit + 1))
        self._z_threshold = z_threshold
        self._rate_limit = rate_limit
        self._rate_window = rate_window_secs
        self._min_baseline = min_baseline

    def _z_score(self, user_id, token_count):
        hist = self._tok_windows[user_id]
        if len(hist) < self._min_baseline:
            return 0.0
        mean = sum(hist) / len(hist)
        variance = sum((x - mean) ** 2 for x in hist) / len(hist)
        std = math.sqrt(variance)
        if std == 0:
            return 0.0
        return (token_count - mean) / std

    def _check_signatures(self, prompt):
        normalized = " ".join(prompt.lower().split())
        return [
            {"type": "INJECTION", "signature": sig}
            for sig in INJECTION_SIGNATURES
            if sig in normalized
        ]

    def _check_rate(self, user_id):
        now = time.time()
        ts = self._ts_windows[user_id]
        ts.append(now)
        recent = sum(1 for t in ts if now - t <= self._rate_window)
        if recent > self._rate_limit:
            return {"type": "RATE_ABUSE", "count": recent,
                    "limit": self._rate_limit,
                    "window": f"{self._rate_window}s"}
        return None

    def check(self, user_id, prompt):
        alerts = []
        token_count = len(prompt.split())
        z = self._z_score(user_id, token_count)
        self._tok_windows[user_id].append(token_count)
        if abs(z) > self._z_threshold:
            alerts.append({"type": "VOLUME_ANOMALY",
                           "z_score": round(z, 2),
                           "tokens": token_count})
        alerts.extend(self._check_signatures(prompt))
        rate_alert = self._check_rate(user_id)
        if rate_alert:
            alerts.append(rate_alert)
        return {"user_id": user_id, "token_count": token_count,
                "z_score": round(z, 2), "alerts": alerts,
                "flagged": bool(alerts), "alert_count": len(alerts)}

    def baseline_size(self, user_id):
        return len(self._tok_windows[user_id])
