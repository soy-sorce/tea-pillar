"""Shared dependency providers for the model service."""

from __future__ import annotations

from threading import Lock

from .predictor import Predictor
from .reward_analyzer import RewardAnalyzer

_predictor: Predictor | None = None
_predictor_lock = Lock()
_reward_analyzer: RewardAnalyzer | None = None
_reward_analyzer_lock = Lock()


def get_predictor() -> Predictor:
    """Lazily initialize the heavy predictor after the container becomes healthy."""
    global _predictor
    if _predictor is None:
        with _predictor_lock:
            if _predictor is None:
                _predictor = Predictor()
    return _predictor


def get_reward_analyzer() -> RewardAnalyzer:
    """Lazily initialize the reward analyzer."""
    global _reward_analyzer
    if _reward_analyzer is None:
        with _reward_analyzer_lock:
            if _reward_analyzer is None:
                _reward_analyzer = RewardAnalyzer()
    return _reward_analyzer
