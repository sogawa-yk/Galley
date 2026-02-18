"""Session関連データモデルのユニットテスト。"""

from datetime import UTC, datetime

from galley.models.session import Answer, HearingResult, Requirement, Session


class TestSession:
    def test_create_session_with_defaults(self) -> None:
        session = Session(id="test-id")
        assert session.id == "test-id"
        assert session.status == "in_progress"
        assert session.answers == {}
        assert session.hearing_result is None

    def test_session_status_in_progress(self) -> None:
        session = Session(id="test-id", status="in_progress")
        assert session.status == "in_progress"

    def test_session_status_completed(self) -> None:
        session = Session(id="test-id", status="completed")
        assert session.status == "completed"

    def test_session_serialization_roundtrip(self) -> None:
        session = Session(id="test-id")
        json_str = session.model_dump_json()
        restored = Session.model_validate_json(json_str)
        assert restored.id == session.id
        assert restored.status == session.status

    def test_session_with_answers(self) -> None:
        answer = Answer(question_id="q1", value="test answer")
        session = Session(id="test-id", answers={"q1": answer})
        assert "q1" in session.answers
        assert session.answers["q1"].value == "test answer"


class TestAnswer:
    def test_create_answer_with_string_value(self) -> None:
        answer = Answer(question_id="q1", value="test answer")
        assert answer.question_id == "q1"
        assert answer.value == "test answer"
        assert answer.answered_at is not None

    def test_create_answer_with_list_value(self) -> None:
        answer = Answer(question_id="q1", value=["option1", "option2"])
        assert answer.value == ["option1", "option2"]

    def test_answer_has_timestamp(self) -> None:
        before = datetime.now(UTC)
        answer = Answer(question_id="q1", value="test")
        after = datetime.now(UTC)
        assert before <= answer.answered_at <= after


class TestRequirement:
    def test_create_requirement(self) -> None:
        req = Requirement(category="compute", description="test", priority="must")
        assert req.category == "compute"
        assert req.priority == "must"

    def test_requirement_priority_values(self) -> None:
        for priority in ("must", "should", "could"):
            req = Requirement(category="compute", description="test", priority=priority)
            assert req.priority == priority


class TestHearingResult:
    def test_create_hearing_result(self) -> None:
        result = HearingResult(
            session_id="test-id",
            summary="Test summary",
            requirements=[],
            constraints=[],
        )
        assert result.session_id == "test-id"
        assert result.summary == "Test summary"
        assert result.completed_at is not None

    def test_hearing_result_with_requirements(self) -> None:
        req = Requirement(category="compute", description="test", priority="must")
        result = HearingResult(
            session_id="test-id",
            summary="Test",
            requirements=[req],
            constraints=["budget constraint"],
        )
        assert len(result.requirements) == 1
        assert len(result.constraints) == 1
