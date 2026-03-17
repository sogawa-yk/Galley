# Domain Entities - Unit 3: Infrastructure Deployment

## Entity: InfraDeployment

デプロイメント全体を管理。

```
InfraDeployment
  - project_name: str
  - compartment_id: str
  - region: str
  - terraform_dir: str          # generated/{name}/terraform/
  - zip_path: str               # generated/{name}/terraform.zip
  - stack_id: str | None        # RM Stack OCID
  - plan_job_id: str | None     # Plan Job OCID
  - apply_job_id: str | None    # Apply Job OCID
  - status: str                 # preparing/planning/applying/succeeded/failed
  - outputs: dict | None        # Terraform outputs
```

## Entity: RMStack

Resource Manager Stack。

```
RMStack
  - stack_id: str               # OCID
  - display_name: str           # {project_name}-stack
  - compartment_id: str
  - terraform_version: str
  - lifecycle_state: str        # CREATING/ACTIVE/DELETING/DELETED/FAILED
  - variables: dict             # Terraform variables
```

## Entity: RMJob

Resource Manager Job。

```
RMJob
  - job_id: str                 # OCID
  - stack_id: str               # 親Stack OCID
  - operation: str              # PLAN/APPLY/DESTROY
  - lifecycle_state: str        # ACCEPTED/IN_PROGRESS/SUCCEEDED/FAILED/CANCELED
  - time_created: str
  - time_finished: str | None
  - logs: str | None            # Jobログ
```

## Entity: CompartmentResolver

コンパートメントID解決。

```
CompartmentResolver
  - resolved_id: str | None     # 解決済みID
  - source: str | None          # instance_metadata/env_var/user_input
  - cached: bool                # キャッシュ済みか
```

## Entity: StackOutputs

Terraform outputs + メタデータ。

```
StackOutputs
  - outputs: dict               # Terraform output key-values
  - _stack_id: str              # Stack OCID
  - _apply_job_id: str          # Apply Job OCID
  - _project_name: str          # プロジェクト名
```

## Entity Relationships

```
InfraDeployment 1---1 CompartmentResolver
InfraDeployment 1---1 RMStack
RMStack 1---* RMJob
InfraDeployment 1---0..1 StackOutputs
```
