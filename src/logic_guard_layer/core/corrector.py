"""Self-correction loop for iterative text repair."""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional

from logic_guard_layer.core.parser import SemanticParser, ParserError
from logic_guard_layer.core.reasoner import ReasoningModule, ConsistencyResult
from logic_guard_layer.llm.client import OpenRouterClient, LLMError
from logic_guard_layer.llm.prompts import get_correction_prompt, CORRECTION_SYSTEM_PROMPT
from logic_guard_layer.models.responses import Violation

logger = logging.getLogger(__name__)


@dataclass
class CorrectionStep:
    """A single step in the correction process."""
    iteration: int
    input_text: str
    output_text: str
    violations: list[Violation]
    is_consistent: bool
    processing_time_ms: float


@dataclass
class CorrectionResult:
    """Result of the complete correction process."""
    original_text: str
    corrected_text: str
    is_consistent: bool
    iterations: int
    max_iterations_reached: bool
    steps: list[CorrectionStep] = field(default_factory=list)
    final_violations: list[Violation] = field(default_factory=list)
    total_processing_time_ms: float = 0.0

    @property
    def was_corrected(self) -> bool:
        """Check if text was modified during correction."""
        return self.original_text != self.corrected_text

    def __str__(self) -> str:
        if self.is_consistent:
            if self.was_corrected:
                return f"Text corrected in {self.iterations} iteration(s)"
            return "Text is already consistent"
        return f"Could not fully correct after {self.iterations} iterations ({len(self.final_violations)} violations remaining)"


class SelfCorrectionLoop:
    """
    Self-correction loop that iteratively repairs inconsistent text.

    Algorithm:
    1. Parse input text
    2. Check consistency against constraints
    3. If consistent → return success
    4. If not consistent:
       a. Check for cycle (seen this output before?)
       b. Generate correction prompt with violations
       c. Call LLM for corrected text
       d. Increment iteration counter
       e. If max_iterations reached → return best result
       f. Go to step 1 with corrected text
    """

    def __init__(
        self,
        llm_client: OpenRouterClient,
        parser: SemanticParser,
        reasoner: ReasoningModule,
        max_iterations: int = 5,
    ):
        """Initialize the self-correction loop.

        Args:
            llm_client: OpenRouter client for LLM calls
            parser: Semantic parser for text extraction
            reasoner: Reasoning module for consistency checking
            max_iterations: Maximum correction attempts (default: 5)
        """
        self.llm_client = llm_client
        self.parser = parser
        self.reasoner = reasoner
        self.max_iterations = max_iterations

    async def correct(self, text: str) -> CorrectionResult:
        """Run the self-correction loop on input text.

        Args:
            text: The text to validate and correct

        Returns:
            CorrectionResult with correction history and final state
        """
        import time

        start_time = time.time()
        original_text = text
        current_text = text
        steps: list[CorrectionStep] = []
        seen_hashes: set[str] = set()
        best_result: Optional[tuple[str, list[Violation]]] = None

        for iteration in range(1, self.max_iterations + 1):
            step_start = time.time()
            logger.info(f"Correction iteration {iteration}/{self.max_iterations}")

            # Check for cycles
            text_hash = self._hash_text(current_text)
            if text_hash in seen_hashes:
                logger.warning(f"Cycle detected at iteration {iteration}")
                break
            seen_hashes.add(text_hash)

            try:
                # Parse the current text
                parsed_data = await self.parser.parse(current_text)
                raw_values = self.parser.extract_raw_values(parsed_data)

                # Check consistency
                consistency = self.reasoner.check_consistency(raw_values)

                step_time = (time.time() - step_start) * 1000

                step = CorrectionStep(
                    iteration=iteration,
                    input_text=current_text,
                    output_text=current_text,
                    violations=consistency.violations,
                    is_consistent=consistency.is_consistent,
                    processing_time_ms=step_time,
                )
                steps.append(step)

                # Track best result (fewest violations)
                if best_result is None or len(consistency.violations) < len(best_result[1]):
                    best_result = (current_text, consistency.violations)

                if consistency.is_consistent:
                    logger.info(f"Text is consistent after {iteration} iteration(s)")
                    total_time = (time.time() - start_time) * 1000
                    return CorrectionResult(
                        original_text=original_text,
                        corrected_text=current_text,
                        is_consistent=True,
                        iterations=iteration,
                        max_iterations_reached=False,
                        steps=steps,
                        final_violations=[],
                        total_processing_time_ms=total_time,
                    )

                # Generate correction
                logger.debug(f"Found {len(consistency.violations)} violations, generating correction")
                corrected_text = await self._generate_correction(
                    current_text,
                    consistency.violations,
                    iteration,
                )

                # Update step with corrected output
                step.output_text = corrected_text
                current_text = corrected_text

            except ParserError as e:
                logger.error(f"Parser error at iteration {iteration}: {e}")
                # Continue with current text, maybe next iteration will work
                continue
            except LLMError as e:
                logger.error(f"LLM error at iteration {iteration}: {e}")
                break

        # Max iterations reached or error - return best result
        total_time = (time.time() - start_time) * 1000

        if best_result:
            final_text, final_violations = best_result
        else:
            final_text = current_text
            final_violations = []

        logger.warning(f"Max iterations reached, returning best result with {len(final_violations)} violations")

        return CorrectionResult(
            original_text=original_text,
            corrected_text=final_text,
            is_consistent=len(final_violations) == 0,
            iterations=len(steps),
            max_iterations_reached=True,
            steps=steps,
            final_violations=final_violations,
            total_processing_time_ms=total_time,
        )

    async def _generate_correction(
        self,
        text: str,
        violations: list[Violation],
        iteration: int,
    ) -> str:
        """Generate corrected text using LLM.

        Args:
            text: The text with violations
            violations: List of constraint violations
            iteration: Current iteration (affects prompt specificity)

        Returns:
            Corrected text from LLM
        """
        # Convert violations to dict format for prompt
        violations_dict = [
            {
                "type": v.type.value,
                "message": v.message,
                "constraint": v.constraint,
                "property": v.property_name,
                "actual": v.actual_value,
                "expected": v.expected_value,
            }
            for v in violations
        ]

        prompt = get_correction_prompt(text, violations_dict, iteration)

        corrected = await self.llm_client.complete(
            prompt=prompt,
            system_prompt=CORRECTION_SYSTEM_PROMPT,
            temperature=0.3,  # Slight variation for creativity in fixes
        )

        return corrected.strip()

    def _hash_text(self, text: str) -> str:
        """Create a hash of text for cycle detection.

        Args:
            text: Text to hash

        Returns:
            SHA256 hash of normalized text
        """
        # Normalize whitespace for comparison
        normalized = " ".join(text.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]


async def create_corrector_from_settings() -> SelfCorrectionLoop:
    """Create a self-correction loop from application settings.

    Returns:
        Configured SelfCorrectionLoop instance
    """
    from logic_guard_layer.config import settings
    from logic_guard_layer.llm.client import create_client_from_settings

    llm_client = create_client_from_settings()
    parser = SemanticParser(llm_client)
    reasoner = ReasoningModule()

    return SelfCorrectionLoop(
        llm_client=llm_client,
        parser=parser,
        reasoner=reasoner,
        max_iterations=settings.max_correction_iterations,
    )
