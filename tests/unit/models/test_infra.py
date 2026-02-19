"""インフラモデルのユニットテスト。"""

from galley.models.infra import CLIResult, RMJob, RMStack, TerraformResult


class TestTerraformResult:
    def test_successful_plan(self) -> None:
        result = TerraformResult(
            success=True,
            command="plan",
            stdout="Plan: 3 to add, 0 to change, 0 to destroy.",
            stderr="",
            exit_code=0,
            plan_summary="3 to add, 0 to change, 0 to destroy",
        )
        assert result.success is True
        assert result.command == "plan"
        assert result.exit_code == 0
        assert result.plan_summary is not None

    def test_failed_plan(self) -> None:
        result = TerraformResult(
            success=False,
            command="plan",
            stdout="",
            stderr="Error: Invalid resource type",
            exit_code=1,
        )
        assert result.success is False
        assert result.exit_code == 1
        assert result.plan_summary is None

    def test_apply_result(self) -> None:
        result = TerraformResult(
            success=True,
            command="apply",
            stdout="Apply complete! Resources: 3 added.",
            stderr="",
            exit_code=0,
        )
        assert result.command == "apply"
        assert result.success is True

    def test_destroy_result(self) -> None:
        result = TerraformResult(
            success=True,
            command="destroy",
            stdout="Destroy complete!",
            stderr="",
            exit_code=0,
        )
        assert result.command == "destroy"

    def test_serialization(self) -> None:
        result = TerraformResult(
            success=True,
            command="plan",
            stdout="output",
            stderr="",
            exit_code=0,
            plan_summary="1 to add, 0 to change, 0 to destroy",
        )
        data = result.model_dump()
        assert data["success"] is True
        assert data["command"] == "plan"
        assert data["plan_summary"] == "1 to add, 0 to change, 0 to destroy"
        # model_validate で復元可能
        restored = TerraformResult.model_validate(data)
        assert restored == result


class TestCLIResult:
    def test_successful_result(self) -> None:
        result = CLIResult(
            success=True,
            stdout='{"data": []}',
            stderr="",
            exit_code=0,
        )
        assert result.success is True
        assert result.exit_code == 0

    def test_failed_result(self) -> None:
        result = CLIResult(
            success=False,
            stdout="",
            stderr="ServiceError: NotAuthorizedOrNotFound",
            exit_code=1,
        )
        assert result.success is False

    def test_serialization(self) -> None:
        result = CLIResult(success=True, stdout="ok", stderr="", exit_code=0)
        data = result.model_dump()
        restored = CLIResult.model_validate(data)
        assert restored == result


class TestRMStack:
    def test_create_stack(self) -> None:
        stack = RMStack(
            id="ocid1.ormstack.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            display_name="test-stack",
            terraform_version="1.5.0",
            lifecycle_state="ACTIVE",
        )
        assert stack.id == "ocid1.ormstack.oc1..test"
        assert stack.lifecycle_state == "ACTIVE"
        assert stack.created_at is not None


class TestRMJob:
    def test_create_job(self) -> None:
        job = RMJob(
            id="ocid1.ormjob.oc1..test",
            stack_id="ocid1.ormstack.oc1..test",
            operation="PLAN",
            lifecycle_state="SUCCEEDED",
        )
        assert job.operation == "PLAN"
        assert job.lifecycle_state == "SUCCEEDED"
        assert job.log_location is None

    def test_job_with_log_location(self) -> None:
        job = RMJob(
            id="ocid1.ormjob.oc1..test",
            stack_id="ocid1.ormstack.oc1..test",
            operation="APPLY",
            lifecycle_state="IN_PROGRESS",
            log_location="https://objectstorage.us-ashburn-1.oraclecloud.com/...",
        )
        assert job.log_location is not None
