"""HearingServiceのユニットテスト。"""

import pytest

from galley.models.errors import HearingAlreadyCompletedError, HearingNotCompletedError
from galley.services.hearing import HearingService


class TestHearingService:
    async def test_create_session_returns_new_session(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        assert session.id is not None
        assert session.status == "in_progress"
        assert session.answers == {}

    async def test_save_answer_stores_answer_in_session(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        answer = await hearing_service.save_answer(session.id, "purpose", "REST API構築")

        assert answer.question_id == "purpose"
        assert answer.value == "REST API構築"

    async def test_save_answer_with_list_value(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        answer = await hearing_service.save_answer(session.id, "workload_type", ["Webアプリケーション", "API サービス"])
        assert answer.value == ["Webアプリケーション", "API サービス"]

    async def test_save_answer_updates_existing(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "初回回答")
        answer = await hearing_service.save_answer(session.id, "purpose", "更新回答")
        assert answer.value == "更新回答"

    async def test_save_answer_raises_error_for_completed_session(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "test")
        await hearing_service.complete_hearing(session.id)

        with pytest.raises(HearingAlreadyCompletedError):
            await hearing_service.save_answer(session.id, "users", "100")

    async def test_save_answers_batch(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        answers = await hearing_service.save_answers_batch(
            session.id,
            [
                {"question_id": "purpose", "value": "REST API構築"},
                {"question_id": "users", "value": "100人"},
            ],
        )
        assert len(answers) == 2
        assert answers[0].question_id == "purpose"
        assert answers[1].question_id == "users"

    async def test_save_answers_batch_raises_error_for_completed_session(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "test")
        await hearing_service.complete_hearing(session.id)

        with pytest.raises(HearingAlreadyCompletedError):
            await hearing_service.save_answers_batch(
                session.id,
                [{"question_id": "users", "value": "100人"}],
            )

    async def test_complete_hearing_generates_result(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "REST API構築")
        await hearing_service.save_answer(session.id, "users", "100人")
        await hearing_service.save_answer(session.id, "workload_type", "API サービス")

        result = await hearing_service.complete_hearing(session.id)
        assert result.session_id == session.id
        assert "REST API構築" in result.summary
        assert len(result.requirements) > 0
        assert result.completed_at is not None

    async def test_complete_hearing_raises_error_for_already_completed(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "test")
        await hearing_service.complete_hearing(session.id)

        with pytest.raises(HearingAlreadyCompletedError):
            await hearing_service.complete_hearing(session.id)

    async def test_get_hearing_result_returns_result(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "REST API構築")
        await hearing_service.complete_hearing(session.id)

        result = await hearing_service.get_hearing_result(session.id)
        assert result.session_id == session.id
        assert "REST API構築" in result.summary

    async def test_get_hearing_result_raises_error_for_incomplete(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()

        with pytest.raises(HearingNotCompletedError):
            await hearing_service.get_hearing_result(session.id)

    async def test_complete_hearing_categorizes_requirements(self, hearing_service: HearingService) -> None:
        session = await hearing_service.create_session()
        await hearing_service.save_answer(session.id, "purpose", "Webアプリケーション")
        await hearing_service.save_answer(session.id, "database_required", "Autonomous Database")
        await hearing_service.save_answer(session.id, "network_requirements", "プライベートのみ")
        await hearing_service.save_answer(session.id, "budget_constraints", "月額10万円以内")

        result = await hearing_service.complete_hearing(session.id)

        categories = {r.category for r in result.requirements}
        assert "database" in categories
        assert "network" in categories
        assert len(result.constraints) > 0
