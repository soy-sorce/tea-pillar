"""Dependency providers for routers."""

from fastapi import Depends

from src.clients.gemini import GeminiClient
from src.clients.model_service import CatModelClient
from src.clients.storage_signer import SignedUrlGenerator
from src.clients.veo import VeoClient
from src.config import Settings, get_settings
from src.repositories.firestore import FirestoreClient
from src.services.bandit.thompson import ThompsonBandit
from src.services.orchestrator import GenerateOrchestrator
from src.services.reward_analysis.service import RewardAnalysisService
from src.services.state_key.builder import StateKeyBuilder
from src.services.storage.reaction_video import ReactionVideoStorageService


def get_firestore_client(settings: Settings = Depends(get_settings)) -> FirestoreClient:
    """Build the Firestore repository."""
    return FirestoreClient(settings=settings)


def get_reaction_video_storage_service(
    settings: Settings = Depends(get_settings),
) -> ReactionVideoStorageService:
    """Build the reaction-video storage service."""
    return ReactionVideoStorageService(settings=settings)


def get_generate_orchestrator(
    settings: Settings = Depends(get_settings),
    firestore_client: FirestoreClient = Depends(get_firestore_client),
) -> GenerateOrchestrator:
    """Build the generation orchestrator."""
    return GenerateOrchestrator(
        settings=settings,
        firestore_client=firestore_client,
        cat_model_client=CatModelClient(settings=settings),
        state_key_builder=StateKeyBuilder(),
        bandit=ThompsonBandit(settings=settings, firestore_client=firestore_client),
        gemini_client=GeminiClient(settings=settings),
        veo_client=VeoClient(settings=settings),
        signed_url_generator=SignedUrlGenerator(settings=settings),
    )


def get_reward_analysis_service(
    settings: Settings = Depends(get_settings),
    firestore_client: FirestoreClient = Depends(get_firestore_client),
) -> RewardAnalysisService:
    """Build the reward-analysis service."""
    return RewardAnalysisService(
        settings=settings,
        firestore_client=firestore_client,
        cat_model_client=CatModelClient(settings=settings),
        bandit=ThompsonBandit(settings=settings, firestore_client=firestore_client),
    )
