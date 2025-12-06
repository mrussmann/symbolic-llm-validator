"""Orchestrator for the Logic-Guard-Layer pipeline."""

import logging
import time
from dataclasses import dataclass
from typing import Optional

from logic_guard_layer.core.corrector import SelfCorrectionLoop, CorrectionResult
from logic_guard_layer.core.parser import SemanticParser
from logic_guard_layer.core.reasoner import ReasoningModule, ConsistencyResult
from logic_guard_layer.llm.client import OpenRouterClient, create_client_from_settings
from logic_guard_layer.models.entities import ParsedData
from logic_guard_layer.models.responses import (
    ValidationResult,
    ValidationResponse,
    Violation,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result from the Logic-Guard-Layer pipeline."""

    # Input
    original_text: str

    # Parsing stage
    parsed_data: Optional[ParsedData] = None
    parse_error: Optional[str] = None

    # Validation stage
    initial_consistency: Optional[ConsistencyResult] = None

    # Correction stage
    correction_result: Optional[CorrectionResult] = None

    # Final output
    final_text: str = ""
    final_parsed_data: Optional[ParsedData] = None
    final_violations: list[Violation] = None

    # Metrics
    total_processing_time_ms: float = 0.0

    def __post_init__(self):
        if self.final_violations is None:
            self.final_violations = []

    @property
    def is_valid(self) -> bool:
        """Check if final result is valid (no violations)."""
        return len(self.final_violations) == 0

    @property
    def was_corrected(self) -> bool:
        """Check if text was modified during processing."""
        return self.original_text != self.final_text

    def to_response(self) -> ValidationResponse:
        """Convert to API response format."""
        return ValidationResponse(
            result=ValidationResult(
                is_valid=self.is_valid,
                violations=self.final_violations,
                corrected_text=self.final_text if self.was_corrected else None,
                iterations=self.correction_result.iterations if self.correction_result else 1,
            ),
            processing_time_ms=self.total_processing_time_ms,
        )


class Orchestrator:
    """
    Main orchestrator for the Logic-Guard-Layer pipeline.

    Pipeline stages:
    1. Parse input text → structured data
    2. Validate against ontology constraints
    3. If invalid, run self-correction loop
    4. Return final validated/corrected result
    """

    def __init__(
        self,
        llm_client: Optional[OpenRouterClient] = None,
        parser: Optional[SemanticParser] = None,
        reasoner: Optional[ReasoningModule] = None,
        corrector: Optional[SelfCorrectionLoop] = None,
        auto_correct: bool = True,
    ):
        """Initialize the orchestrator.

        Args:
            llm_client: OpenRouter client (created from settings if not provided)
            parser: Semantic parser (created with llm_client if not provided)
            reasoner: Reasoning module (created with defaults if not provided)
            corrector: Self-correction loop (created if not provided)
            auto_correct: Whether to automatically correct invalid input
        """
        self.llm_client = llm_client
        self.parser = parser
        self.reasoner = reasoner or ReasoningModule()
        self.corrector = corrector
        self.auto_correct = auto_correct
        self._initialized = False

    async def _ensure_initialized(self):
        """Lazily initialize components that need async setup."""
        if self._initialized:
            return

        if self.llm_client is None:
            self.llm_client = create_client_from_settings()

        if self.parser is None:
            self.parser = SemanticParser(self.llm_client)

        if self.corrector is None:
            self.corrector = SelfCorrectionLoop(
                llm_client=self.llm_client,
                parser=self.parser,
                reasoner=self.reasoner,
            )

        self._initialized = True

    async def process(self, text: str) -> PipelineResult:
        """Process text through the complete pipeline.

        Args:
            text: Input text to validate and potentially correct

        Returns:
            PipelineResult with all processing details
        """
        start_time = time.time()
        await self._ensure_initialized()

        result = PipelineResult(original_text=text)

        try:
            # Stage 1: Parse
            logger.info("Stage 1: Parsing input text")
            parsed_data = await self.parser.parse(text)
            result.parsed_data = parsed_data
            raw_values = self.parser.extract_raw_values(parsed_data)

            # Stage 2: Validate
            logger.info("Stage 2: Validating against constraints")
            consistency = self.reasoner.check_consistency(raw_values)
            result.initial_consistency = consistency

            if consistency.is_consistent:
                # Already valid, no correction needed
                logger.info("Input is already consistent")
                result.final_text = text
                result.final_parsed_data = parsed_data
                result.final_violations = []
            elif self.auto_correct:
                # Stage 3: Correct
                logger.info(f"Stage 3: Correcting {len(consistency.violations)} violations")
                correction = await self.corrector.correct(text)
                result.correction_result = correction
                result.final_text = correction.corrected_text
                result.final_violations = correction.final_violations

                # Re-parse corrected text for final data
                if correction.is_consistent:
                    final_parsed = await self.parser.parse(correction.corrected_text)
                    result.final_parsed_data = final_parsed
                else:
                    result.final_parsed_data = parsed_data
            else:
                # No auto-correction, return as-is with violations
                result.final_text = text
                result.final_parsed_data = parsed_data
                result.final_violations = consistency.violations

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result.parse_error = str(e)
            result.final_text = text
            result.final_violations = []

        result.total_processing_time_ms = (time.time() - start_time) * 1000
        logger.info(f"Pipeline completed in {result.total_processing_time_ms:.2f}ms")

        return result

    async def validate_only(self, text: str) -> PipelineResult:
        """Validate text without correction.

        Args:
            text: Input text to validate

        Returns:
            PipelineResult with validation results only
        """
        original_auto_correct = self.auto_correct
        self.auto_correct = False
        try:
            return await self.process(text)
        finally:
            self.auto_correct = original_auto_correct

    async def get_constraints_info(self) -> list[dict]:
        """Get information about all active constraints.

        Returns:
            List of constraint information dictionaries
        """
        return self.reasoner.get_constraints_summary()

    async def close(self):
        """Clean up resources."""
        if self.llm_client is not None:
            await self.llm_client.close()


# Singleton orchestrator instance
_orchestrator: Optional[Orchestrator] = None


async def get_orchestrator() -> Orchestrator:
    """Get or create the singleton orchestrator instance.

    Returns:
        Configured Orchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


async def reset_orchestrator():
    """Reset the singleton orchestrator (useful for testing)."""
    global _orchestrator
    if _orchestrator is not None:
        await _orchestrator.close()
        _orchestrator = None
