"""Tests for Orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from logic_guard_layer.core.orchestrator import (
    Orchestrator,
    PipelineResult,
    get_orchestrator,
    reset_orchestrator,
)
from logic_guard_layer.core.corrector import CorrectionResult
from logic_guard_layer.core.reasoner import ConsistencyResult
from logic_guard_layer.models.entities import ParsedData, Component, ComponentType
from logic_guard_layer.models.responses import Violation, ViolationType


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_create_pipeline_result(self):
        """Test creating a pipeline result."""
        result = PipelineResult(original_text="Test text")
        assert result.original_text == "Test text"
        assert result.final_violations == []
        assert result.is_valid is True

    def test_is_valid_no_violations(self):
        """Test is_valid with no violations."""
        result = PipelineResult(
            original_text="Test",
            final_violations=[]
        )
        assert result.is_valid is True

    def test_is_valid_with_violations(self, sample_violation):
        """Test is_valid with violations."""
        result = PipelineResult(
            original_text="Test",
            final_violations=[sample_violation]
        )
        assert result.is_valid is False

    def test_was_corrected_true(self):
        """Test was_corrected when text changed."""
        result = PipelineResult(
            original_text="Original",
            final_text="Corrected"
        )
        assert result.was_corrected is True

    def test_was_corrected_false(self):
        """Test was_corrected when text unchanged."""
        result = PipelineResult(
            original_text="Same",
            final_text="Same"
        )
        assert result.was_corrected is False


class TestOrchestratorInit:
    """Tests for Orchestrator initialization."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        orchestrator = Orchestrator()
        assert orchestrator.llm_client is None
        assert orchestrator.parser is None
        assert orchestrator.reasoner is not None
        assert orchestrator.corrector is None
        assert orchestrator.auto_correct is True
        assert orchestrator._initialized is False

    def test_init_custom_components(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test initialization with custom components."""
        from logic_guard_layer.core.corrector import SelfCorrectionLoop

        mock_corrector = MagicMock(spec=SelfCorrectionLoop)

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            corrector=mock_corrector,
            auto_correct=False
        )

        assert orchestrator.llm_client is mock_llm_client
        assert orchestrator.parser is mock_parser
        assert orchestrator.reasoner is mock_reasoner
        assert orchestrator.corrector is mock_corrector
        assert orchestrator.auto_correct is False


class TestOrchestratorEnsureInitialized:
    """Tests for Orchestrator._ensure_initialized method."""

    @pytest.mark.asyncio
    async def test_ensure_initialized_creates_components(self):
        """Test _ensure_initialized creates components."""
        with patch("logic_guard_layer.core.orchestrator.create_client_from_settings") as mock_create:
            mock_client = AsyncMock()
            mock_create.return_value = mock_client

            orchestrator = Orchestrator()
            await orchestrator._ensure_initialized()

            assert orchestrator._initialized is True
            assert orchestrator.llm_client is not None
            assert orchestrator.parser is not None
            assert orchestrator.corrector is not None

    @pytest.mark.asyncio
    async def test_ensure_initialized_idempotent(self):
        """Test _ensure_initialized only runs once."""
        with patch("logic_guard_layer.core.orchestrator.create_client_from_settings") as mock_create:
            mock_client = AsyncMock()
            mock_create.return_value = mock_client

            orchestrator = Orchestrator()
            await orchestrator._ensure_initialized()
            await orchestrator._ensure_initialized()

            # Should only call create once
            mock_create.assert_called_once()


class TestOrchestratorProcess:
    """Tests for Orchestrator.process method."""

    @pytest.mark.asyncio
    async def test_process_valid_text(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test processing valid text."""
        # Setup mock reasoner to return consistent
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )
        orchestrator._initialized = True

        result = await orchestrator.process("Valid text")

        assert result.is_valid is True
        assert len(result.final_violations) == 0
        assert result.final_text == "Valid text"
        assert result.was_corrected is False

    @pytest.mark.asyncio
    async def test_process_invalid_with_auto_correct(self, mock_llm_client, mock_parser, sample_violation):
        """Test processing invalid text with auto-correction."""
        # Setup mock reasoner
        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        # Setup mock corrector
        mock_corrector = MagicMock()
        mock_corrector.correct = AsyncMock(return_value=CorrectionResult(
            original_text="Invalid text",
            corrected_text="Corrected text",
            is_consistent=True,
            iterations=2,
            max_iterations_reached=False,
            final_violations=[]
        ))

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            corrector=mock_corrector,
            auto_correct=True
        )
        orchestrator._initialized = True

        result = await orchestrator.process("Invalid text")

        assert result.final_text == "Corrected text"
        mock_corrector.correct.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_invalid_without_auto_correct(self, mock_llm_client, mock_parser, sample_violation):
        """Test processing invalid text without auto-correction."""
        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            auto_correct=False
        )
        orchestrator._initialized = True

        result = await orchestrator.process("Invalid text")

        assert result.is_valid is False
        assert len(result.final_violations) == 1
        assert result.final_text == "Invalid text"

    @pytest.mark.asyncio
    async def test_process_handles_parser_error(self, mock_llm_client, mock_reasoner):
        """Test processing handles parser errors."""
        from logic_guard_layer.core.parser import ParserError

        mock_parser = MagicMock()
        mock_parser.parse = AsyncMock(side_effect=ParserError("Parse failed"))

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )
        orchestrator._initialized = True

        result = await orchestrator.process("Some text")

        assert result.parse_error is not None
        assert "Parse failed" in result.parse_error

    @pytest.mark.asyncio
    async def test_process_records_timing(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test processing records timing."""
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )
        orchestrator._initialized = True

        result = await orchestrator.process("Text")

        assert result.total_processing_time_ms >= 0


class TestOrchestratorValidateOnly:
    """Tests for Orchestrator.validate_only method."""

    @pytest.mark.asyncio
    async def test_validate_only_disables_correction(self, mock_llm_client, mock_parser, sample_violation):
        """Test validate_only disables auto-correction."""
        mock_reasoner = MagicMock()
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        mock_corrector = MagicMock()
        mock_corrector.correct = AsyncMock()

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            corrector=mock_corrector,
            auto_correct=True
        )
        orchestrator._initialized = True

        result = await orchestrator.validate_only("Invalid text")

        # Should not call corrector
        mock_corrector.correct.assert_not_called()
        assert len(result.final_violations) == 1

    @pytest.mark.asyncio
    async def test_validate_only_restores_auto_correct(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test validate_only restores auto_correct setting."""
        mock_reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.0
        ))

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner,
            auto_correct=True
        )
        orchestrator._initialized = True

        assert orchestrator.auto_correct is True
        await orchestrator.validate_only("Text")
        assert orchestrator.auto_correct is True


class TestOrchestratorGetConstraintsInfo:
    """Tests for Orchestrator.get_constraints_info method."""

    @pytest.mark.asyncio
    async def test_get_constraints_info(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test getting constraints info."""
        mock_reasoner.get_constraints_summary = MagicMock(return_value=[
            {"id": "C1", "name": "Test constraint"}
        ])

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        info = await orchestrator.get_constraints_info()

        assert len(info) == 1
        assert info[0]["id"] == "C1"


class TestOrchestratorClose:
    """Tests for Orchestrator.close method."""

    @pytest.mark.asyncio
    async def test_close_client(self, mock_llm_client, mock_parser, mock_reasoner):
        """Test closing the LLM client."""
        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        await orchestrator.close()

        mock_llm_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_client(self, mock_parser, mock_reasoner):
        """Test closing when no client."""
        orchestrator = Orchestrator(
            parser=mock_parser,
            reasoner=mock_reasoner
        )

        # Should not raise
        await orchestrator.close()


class TestOrchestratorSingleton:
    """Tests for orchestrator singleton functions."""

    @pytest.mark.asyncio
    async def test_get_orchestrator_creates_instance(self):
        """Test get_orchestrator creates instance."""
        import logic_guard_layer.core.orchestrator as orch_module
        orch_module._orchestrator = None

        with patch("logic_guard_layer.core.orchestrator.Orchestrator") as MockOrch:
            mock_instance = MagicMock()
            MockOrch.return_value = mock_instance

            result = await get_orchestrator()

            assert result is mock_instance

        orch_module._orchestrator = None

    @pytest.mark.asyncio
    async def test_get_orchestrator_returns_same_instance(self):
        """Test get_orchestrator returns same instance."""
        import logic_guard_layer.core.orchestrator as orch_module
        orch_module._orchestrator = None

        with patch("logic_guard_layer.core.orchestrator.Orchestrator") as MockOrch:
            mock_instance = MagicMock()
            MockOrch.return_value = mock_instance

            result1 = await get_orchestrator()
            result2 = await get_orchestrator()

            assert result1 is result2
            MockOrch.assert_called_once()

        orch_module._orchestrator = None

    @pytest.mark.asyncio
    async def test_reset_orchestrator(self):
        """Test reset_orchestrator clears instance."""
        import logic_guard_layer.core.orchestrator as orch_module

        mock_orch = MagicMock()
        mock_orch.close = AsyncMock()
        orch_module._orchestrator = mock_orch

        await reset_orchestrator()

        mock_orch.close.assert_called_once()
        assert orch_module._orchestrator is None

    @pytest.mark.asyncio
    async def test_reset_orchestrator_none(self):
        """Test reset_orchestrator when no instance."""
        import logic_guard_layer.core.orchestrator as orch_module
        orch_module._orchestrator = None

        # Should not raise
        await reset_orchestrator()

        assert orch_module._orchestrator is None


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator."""

    @pytest.mark.asyncio
    async def test_full_valid_workflow(self, mock_llm_client):
        """Test complete workflow with valid data."""
        from logic_guard_layer.core.reasoner import ReasoningModule

        # Create real reasoner
        reasoner = ReasoningModule()

        # Create mock parser returning valid data
        mock_parser = MagicMock()
        mock_parser.parse = AsyncMock(return_value=ParsedData(
            components=[Component(
                name="HP-001",
                type=ComponentType.HYDRAULIC_PUMP,
                operating_hours=5000,
                max_lifespan=20000,
                maintenance_interval=2500
            )],
            raw_values={}
        ))
        mock_parser.extract_raw_values = MagicMock(return_value={
            "name": "HP-001",
            "operating_hours": 5000,
            "max_lifespan": 20000,
            "maintenance_interval": 2500,
        })

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=reasoner,
            auto_correct=True
        )
        orchestrator._initialized = True

        result = await orchestrator.process("Valid maintenance text")

        assert result.is_valid is True
        assert result.was_corrected is False
        assert result.parsed_data is not None

    @pytest.mark.asyncio
    async def test_workflow_with_correction(self, mock_llm_client):
        """Test workflow that requires correction."""
        from logic_guard_layer.core.reasoner import ReasoningModule

        reasoner = ReasoningModule()

        # Parser returns invalid data first, then valid after correction
        call_count = [0]

        async def mock_parse(text):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call - invalid data
                return ParsedData(
                    components=[Component(
                        name="HP-001",
                        operating_hours=25000,  # Exceeds lifespan
                        max_lifespan=20000
                    )],
                    raw_values={}
                )
            else:
                # After correction - valid data
                return ParsedData(
                    components=[Component(
                        name="HP-001",
                        operating_hours=15000,
                        max_lifespan=20000
                    )],
                    raw_values={}
                )

        def mock_extract(parsed_data):
            if parsed_data.components:
                comp = parsed_data.components[0]
                return {
                    "name": comp.name,
                    "operating_hours": comp.operating_hours,
                    "max_lifespan": comp.max_lifespan,
                }
            return {}

        mock_parser = MagicMock()
        mock_parser.parse = mock_parse
        mock_parser.extract_raw_values = mock_extract

        mock_llm_client.complete = AsyncMock(return_value="Corrected text with 15000 hours")

        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=reasoner,
            auto_correct=True
        )
        orchestrator._initialized = True

        # Need to create corrector manually since it needs parser/reasoner
        from logic_guard_layer.core.corrector import SelfCorrectionLoop
        orchestrator.corrector = SelfCorrectionLoop(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=reasoner
        )

        result = await orchestrator.process("Invalid text with 25000 hours")

        assert result.initial_consistency is not None
        assert result.initial_consistency.is_consistent is False
