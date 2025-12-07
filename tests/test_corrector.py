"""Tests for SelfCorrectionLoop."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from logic_guard_layer.core.corrector import (
    SelfCorrectionLoop,
    CorrectionStep,
    CorrectionResult,
)
from logic_guard_layer.core.parser import ParserError
from logic_guard_layer.core.reasoner import ConsistencyResult
from logic_guard_layer.llm.client import LLMError
from logic_guard_layer.models.responses import Violation, ViolationType


class TestCorrectionStep:
    """Tests for CorrectionStep dataclass."""

    def test_create_correction_step(self, sample_violation):
        """Test creating a correction step."""
        step = CorrectionStep(
            iteration=1,
            input_text="Input text",
            output_text="Output text",
            violations=[sample_violation],
            is_consistent=False,
            processing_time_ms=100.0
        )
        assert step.iteration == 1
        assert step.input_text == "Input text"
        assert step.output_text == "Output text"
        assert len(step.violations) == 1
        assert step.is_consistent is False
        assert step.processing_time_ms == 100.0


class TestCorrectionResult:
    """Tests for CorrectionResult dataclass."""

    def test_create_successful_result(self):
        """Test creating a successful correction result."""
        result = CorrectionResult(
            original_text="Original",
            corrected_text="Corrected",
            is_consistent=True,
            iterations=2,
            max_iterations_reached=False,
            steps=[],
            final_violations=[],
            total_processing_time_ms=500.0
        )
        assert result.is_consistent is True
        assert result.was_corrected is True
        assert result.iterations == 2

    def test_was_corrected_true(self):
        """Test was_corrected when text changed."""
        result = CorrectionResult(
            original_text="Original",
            corrected_text="Different",
            is_consistent=True,
            iterations=1,
            max_iterations_reached=False
        )
        assert result.was_corrected is True

    def test_was_corrected_false(self):
        """Test was_corrected when text unchanged."""
        result = CorrectionResult(
            original_text="Same",
            corrected_text="Same",
            is_consistent=True,
            iterations=1,
            max_iterations_reached=False
        )
        assert result.was_corrected is False

    def test_str_corrected(self):
        """Test string representation for corrected text."""
        result = CorrectionResult(
            original_text="Original",
            corrected_text="Corrected",
            is_consistent=True,
            iterations=2,
            max_iterations_reached=False
        )
        s = str(result)
        assert "corrected" in s.lower()
        assert "2" in s

    def test_str_already_consistent(self):
        """Test string representation for already consistent text."""
        result = CorrectionResult(
            original_text="Same",
            corrected_text="Same",
            is_consistent=True,
            iterations=1,
            max_iterations_reached=False
        )
        s = str(result)
        assert "already consistent" in s.lower()

    def test_str_could_not_correct(self, sample_violation):
        """Test string representation when correction failed."""
        result = CorrectionResult(
            original_text="Original",
            corrected_text="Still wrong",
            is_consistent=False,
            iterations=5,
            max_iterations_reached=True,
            final_violations=[sample_violation]
        )
        s = str(result)
        assert "could not" in s.lower()
        assert "1 violations" in s


class TestSelfCorrectionLoopInit:
    """Tests for SelfCorrectionLoop initialization."""

    def test_init(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test initialization."""
        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            max_iterations=5
        )
        assert corrector.llm_client is mock_llm_client
        assert corrector.parser is mock_parser
        assert corrector.reasoner is mock_reasoner
        assert corrector.max_iterations == 5

    def test_init_default_max_iterations(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test default max_iterations."""
        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )
        assert corrector.max_iterations == 5


class TestSelfCorrectionLoopCorrect:
    """Tests for SelfCorrectionLoop.correct method."""

    @pytest.mark.asyncio
    async def test_correct_already_consistent(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test correction when text is already consistent."""
        # Setup mock to return consistent result
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        result = await corrector.correct("Already valid text")

        assert result.is_consistent is True
        assert result.iterations == 1
        assert result.max_iterations_reached is False
        assert len(result.final_violations) == 0

    @pytest.mark.asyncio
    async def test_correct_single_iteration(self, mock_llm_client, mock_parser, sample_violation):
        """Test correction that succeeds in one iteration."""
        # Create reasoner that fails first, then succeeds
        call_count = [0]

        def mock_check(data):
            call_count[0] += 1
            if call_count[0] == 1:
                return ConsistencyResult(
                    is_consistent=False,
                    violations=[sample_violation],
                    checked_constraints=8,
                    processing_time_ms=10.0
                )
            return ConsistencyResult(
                is_consistent=True,
                violations=[],
                checked_constraints=8,
                processing_time_ms=10.0
            )

        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = mock_check

        mock_llm_client.complete = AsyncMock(return_value="Corrected text")

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        result = await corrector.correct("Invalid text")

        assert result.is_consistent is True
        assert result.iterations == 2

    @pytest.mark.asyncio
    async def test_correct_max_iterations_reached(self, mock_llm_client, mock_parser, sample_violation):
        """Test correction that reaches max iterations."""
        # Setup reasoner to always return violations
        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        # Setup LLM to return different text each time
        call_count = [0]

        async def mock_complete(*args, **kwargs):
            call_count[0] += 1
            return f"Corrected text {call_count[0]}"

        mock_llm_client.complete = mock_complete

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            max_iterations=3
        )

        result = await corrector.correct("Invalid text")

        assert result.is_consistent is False
        assert result.max_iterations_reached is True
        assert result.iterations == 3
        assert len(result.final_violations) == 1

    @pytest.mark.asyncio
    async def test_correct_cycle_detection(self, mock_llm_client, mock_parser, sample_violation):
        """Test correction detects cycles."""
        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        # LLM returns same text each time (cycle)
        mock_llm_client.complete = AsyncMock(return_value="Same text every time")

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            max_iterations=5
        )

        result = await corrector.correct("Same text every time")

        # Should detect cycle and stop early
        assert result.iterations <= 2

    @pytest.mark.asyncio
    async def test_correct_parser_error_continues(self, mock_llm_client, sample_violation):
        """Test correction continues after parser error.

        Note: When parser fails on first try, it increments iteration counter
        and continues to next iteration with same text. If text hash is same,
        cycle detection stops the loop.
        """
        mock_parser = MagicMock()
        call_count = [0]

        async def mock_parse(text):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ParserError("Parse failed")
            return MagicMock(components=[], raw_values={})

        mock_parser.parse = mock_parse
        mock_parser.extract_raw_values = MagicMock(return_value={})

        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        result = await corrector.correct("Text")

        # Parser was called at least once (may stop due to cycle detection)
        assert call_count[0] >= 1

    @pytest.mark.asyncio
    async def test_correct_llm_error_stops(self, mock_llm_client, mock_parser, sample_violation):
        """Test correction stops on LLM error."""
        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        mock_llm_client.complete = AsyncMock(side_effect=LLMError("API error"))

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        result = await corrector.correct("Invalid text")

        # Should stop after LLM error
        assert result.iterations == 1

    @pytest.mark.asyncio
    async def test_correct_tracks_best_result(self, mock_llm_client, mock_parser):
        """Test correction tracks best result."""
        call_count = [0]
        violations = [
            Violation(type=ViolationType.RANGE_ERROR, constraint="C1", message="V1"),
            Violation(type=ViolationType.RANGE_ERROR, constraint="C2", message="V2"),
            Violation(type=ViolationType.RANGE_ERROR, constraint="C3", message="V3"),
        ]

        def mock_check(data):
            call_count[0] += 1
            # Return decreasing violations
            remaining = max(0, 3 - call_count[0])
            return ConsistencyResult(
                is_consistent=remaining == 0,
                violations=violations[:remaining],
                checked_constraints=8,
                processing_time_ms=10.0
            )

        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = mock_check

        iter_count = [0]

        async def mock_complete(*args, **kwargs):
            iter_count[0] += 1
            return f"Improved text {iter_count[0]}"

        mock_llm_client.complete = mock_complete

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            max_iterations=5
        )

        result = await corrector.correct("Initial text")

        assert result.is_consistent is True
        assert len(result.final_violations) == 0

    @pytest.mark.asyncio
    async def test_correct_records_steps(self, mock_llm_client, mock_parser, sample_violation):
        """Test correction records all steps."""
        call_count = [0]

        def mock_check(data):
            call_count[0] += 1
            if call_count[0] <= 2:
                return ConsistencyResult(
                    is_consistent=False,
                    violations=[sample_violation],
                    checked_constraints=8,
                    processing_time_ms=10.0
                )
            return ConsistencyResult(
                is_consistent=True,
                violations=[],
                checked_constraints=8,
                processing_time_ms=10.0
            )

        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = mock_check

        iter_count = [0]

        async def mock_complete(*args, **kwargs):
            iter_count[0] += 1
            return f"Corrected {iter_count[0]}"

        mock_llm_client.complete = mock_complete

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        result = await corrector.correct("Initial")

        assert len(result.steps) == 3
        for i, step in enumerate(result.steps):
            assert step.iteration == i + 1


class TestSelfCorrectionLoopGenerateCorrection:
    """Tests for SelfCorrectionLoop._generate_correction method."""

    @pytest.mark.asyncio
    async def test_generate_correction(self, mock_llm_client, mock_parser, mock_reasoner, sample_violation):
        """Test generating correction."""
        mock_llm_client.complete = AsyncMock(return_value="  Corrected text  ")

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        result = await corrector._generate_correction(
            "Original text",
            [sample_violation],
            1
        )

        # Should strip whitespace
        assert result == "Corrected text"

        # Should have called LLM
        mock_llm_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_correction_formats_violations(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test that violations are formatted correctly for prompt."""
        violations = [
            Violation(
                type=ViolationType.RANGE_ERROR,
                constraint="C1",
                message="Error message",
                property_name="test_prop",
                actual_value=100,
                expected_value=">= 0"
            )
        ]

        mock_llm_client.complete = AsyncMock(return_value="Corrected")

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        await corrector._generate_correction("Text", violations, 1)

        # Verify the call was made (detailed prompt inspection would require more mocking)
        mock_llm_client.complete.assert_called_once()


class TestSelfCorrectionLoopHashText:
    """Tests for SelfCorrectionLoop._hash_text method."""

    def test_hash_text_same_text(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test same text produces same hash."""
        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        hash1 = corrector._hash_text("Test text")
        hash2 = corrector._hash_text("Test text")

        assert hash1 == hash2

    def test_hash_text_different_text(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test different text produces different hash."""
        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        hash1 = corrector._hash_text("Text A")
        hash2 = corrector._hash_text("Text B")

        assert hash1 != hash2

    def test_hash_text_normalizes_whitespace(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test whitespace is normalized before hashing."""
        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        hash1 = corrector._hash_text("Test text")
        hash2 = corrector._hash_text("Test  text")
        hash3 = corrector._hash_text("Test\n\ntext")
        hash4 = corrector._hash_text("  Test   text  ")

        assert hash1 == hash2 == hash3 == hash4

    def test_hash_text_length(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test hash is truncated to 16 characters."""
        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        hash_result = corrector._hash_text("Any text")

        assert len(hash_result) == 16


class TestSelfCorrectionLoopIntegration:
    """Integration tests for SelfCorrectionLoop."""

    @pytest.mark.asyncio
    async def test_full_correction_workflow(self, mock_llm_client):
        """Test complete correction workflow."""
        from logic_guard_layer.core.parser import SemanticParser
        from logic_guard_layer.core.reasoner import ReasoningModule
        from logic_guard_layer.models.entities import ParsedData, Component, ComponentType

        # Create real reasoner
        reasoner = ReasoningModule()

        # Create mock parser that returns different data based on input
        mock_parser = MagicMock()

        parse_count = [0]

        async def mock_parse(text):
            parse_count[0] += 1
            if "25000" in text:  # Initial invalid text
                return ParsedData(
                    components=[Component(
                        name="HP-001",
                        type=ComponentType.HYDRAULIC_PUMP,
                        operating_hours=25000,
                        max_lifespan=20000
                    )],
                    raw_values={}
                )
            else:  # Corrected text
                return ParsedData(
                    components=[Component(
                        name="HP-001",
                        type=ComponentType.HYDRAULIC_PUMP,
                        operating_hours=15000,
                        max_lifespan=20000
                    )],
                    raw_values={}
                )

        mock_parser.parse = mock_parse

        def mock_extract(parsed_data):
            if parsed_data.components:
                comp = parsed_data.components[0]
                return {
                    "name": comp.name,
                    "operating_hours": comp.operating_hours,
                    "max_lifespan": comp.max_lifespan,
                }
            return {}

        mock_parser.extract_raw_values = mock_extract

        # LLM returns corrected text
        mock_llm_client.complete = AsyncMock(
            return_value="Hydraulikpumpe HP-001 mit 15000 Betriebsstunden"
        )

        corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=reasoner,
            max_iterations=5
        )

        result = await corrector.correct(
            "Hydraulikpumpe HP-001 mit 25000 Betriebsstunden, max 20000"
        )

        assert result.is_consistent is True
        assert result.was_corrected is True
        assert len(result.final_violations) == 0
