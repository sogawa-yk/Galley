import { z } from 'zod';

// ===== データモデルスキーマ =====

export const EstimationSchema = z.object({
  confidence_label: z.enum(['public_reference', 'general_estimate']),
  reasoning: z.string(),
  source_info: z.string().optional(),
});

export const AnsweredItemSchema = z.object({
  value: z.union([z.string(), z.number(), z.boolean()]),
  source: z.enum(['user_selected', 'user_free_text', 'estimated', 'not_answered']),
  estimation: EstimationSchema.optional(),
});

export const SessionSchema = z.object({
  session_id: z.string().uuid(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  status: z.enum(['in_progress', 'completed']),
  project_description: z.string(),
});

export const HearingResultSchema = z.object({
  metadata: z.object({
    hearing_id: z.string().uuid(),
    created_at: z.string().datetime(),
    updated_at: z.string().datetime().optional(),
    version: z.literal('1.0.0'),
    status: z.enum(['in_progress', 'completed']),
  }),
  project_overview: z.object({
    description: z.string(),
    industry: AnsweredItemSchema.optional(),
    project_type: AnsweredItemSchema.optional(),
  }),
  requirements: z.object({
    scale: z
      .object({
        concurrent_users: AnsweredItemSchema.optional(),
        total_users: AnsweredItemSchema.optional(),
      })
      .optional(),
    traffic: z
      .object({
        spike_pattern: AnsweredItemSchema.optional(),
        peak_tps: AnsweredItemSchema.optional(),
      })
      .optional(),
    database: z
      .object({
        existing_db: AnsweredItemSchema.optional(),
        migration_required: AnsweredItemSchema.optional(),
        data_volume: AnsweredItemSchema.optional(),
      })
      .optional(),
    network: z
      .object({
        multi_region: AnsweredItemSchema.optional(),
        on_premises_connection: AnsweredItemSchema.optional(),
      })
      .optional(),
    security: z
      .object({
        auth_method: AnsweredItemSchema.optional(),
        compliance: AnsweredItemSchema.optional(),
      })
      .optional(),
    availability: z
      .object({
        sla_target: AnsweredItemSchema.optional(),
        dr_requirement: AnsweredItemSchema.optional(),
        backup_policy: AnsweredItemSchema.optional(),
      })
      .optional(),
    performance: z
      .object({
        latency_requirement: AnsweredItemSchema.optional(),
        throughput_requirement: AnsweredItemSchema.optional(),
      })
      .optional(),
    operations: z
      .object({
        monitoring: AnsweredItemSchema.optional(),
        log_retention: AnsweredItemSchema.optional(),
      })
      .optional(),
    budget_schedule: z
      .object({
        cost_constraint: AnsweredItemSchema.optional(),
        demo_deadline: AnsweredItemSchema.optional(),
      })
      .optional(),
  }),
});

export const ComponentSchema = z.object({
  category: z.string(),
  service_name: z.string(),
  purpose: z.string(),
  reason: z.string(),
});

export const WarningSchema = z.object({
  type: z.string(),
  message: z.string(),
  severity: z.enum(['error', 'warning', 'info']),
});

export const ArchitectureOutputSchema = z.object({
  session_id: z.string().uuid(),
  components: z.array(ComponentSchema),
  decisions: z.array(
    z.object({
      category: z.string(),
      decision: z.string(),
      reason: z.string(),
    }),
  ),
  warnings: z.array(WarningSchema),
});

// ===== Tool引数スキーマ =====

export const CreateSessionArgsSchema = z.object({
  project_description: z.string().min(1).max(5000),
});

export const CategoryEnum = z.enum([
  'project_overview',
  'scale',
  'traffic',
  'database',
  'network',
  'security',
  'availability',
  'performance',
  'operations',
  'budget_schedule',
]);

export const SaveAnswerArgsSchema = z.object({
  session_id: z.string().uuid(),
  question_id: z.string(),
  category: CategoryEnum,
  value: z.union([z.string(), z.number(), z.boolean()]),
  source: z.enum(['user_selected', 'user_free_text', 'estimated', 'not_answered']),
  estimation: EstimationSchema.optional(),
});

export const SaveAnswersBatchArgsSchema = z.object({
  session_id: z.string().uuid(),
  answers: z.array(SaveAnswerArgsSchema.omit({ session_id: true })),
});

export const SessionIdArgsSchema = z.object({
  session_id: z.string().uuid(),
});

export const ListSessionsArgsSchema = z.object({
  status: z.enum(['in_progress', 'completed']).optional(),
});

export const SaveArchitectureArgsSchema = z.object({
  session_id: z.string().uuid(),
  components: z.array(ComponentSchema),
  decisions: z.array(
    z.object({
      category: z.string(),
      decision: z.string(),
      reason: z.string(),
    }),
  ),
  warnings: z.array(WarningSchema).optional().default([]),
});

export const ExportMermaidArgsSchema = z.object({
  session_id: z.string().uuid(),
  mermaid_code: z.string().min(1),
});

export const ExportIacArgsSchema = z.object({
  session_id: z.string().uuid(),
  files: z
    .array(
      z.object({
        name: z.string(),
        content: z.string(),
      }),
    )
    .min(1),
});

export const ExportAllArgsSchema = z.object({
  session_id: z.string().uuid(),
  mermaid_code: z.string().optional(),
  iac_files: z
    .array(
      z.object({
        name: z.string(),
        content: z.string(),
      }),
    )
    .optional(),
});

// ===== 設定ファイルスキーマ =====

export const HearingQuestionsConfigSchema = z.object({
  version: z.string(),
  categories: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      required: z.boolean().optional().default(true),
      description: z.string().optional(),
    }),
  ),
});

export const HearingFlowConfigSchema = z.object({
  version: z.string(),
  default_order: z.array(z.string()),
  conditional_rules: z
    .array(
      z.object({
        condition: z.string(),
        add_categories: z.array(z.string()).optional(),
        skip_categories: z.array(z.string()).optional(),
      }),
    )
    .optional()
    .default([]),
});

export const OciServicesConfigSchema = z.object({
  version: z.string(),
  services: z.array(
    z.object({
      name: z.string(),
      category: z.string(),
      description: z.string(),
      use_cases: z.array(z.string()).optional(),
      constraints: z.array(z.string()).optional(),
    }),
  ),
});

export const OciArchitecturesConfigSchema = z.object({
  version: z.string(),
  patterns: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      description: z.string(),
      components: z.array(z.string()),
      applicable_industries: z.array(z.string()).optional(),
    }),
  ),
});

export const OciTerraformConfigSchema = z.object({
  version: z.string(),
  provider: z
    .object({
      example: z.string(),
    })
    .optional(),
  resource_manager_schema: z
    .object({
      description: z.string(),
      example: z.string(),
      variable_types: z
        .array(
          z.object({
            type: z.string(),
            description: z.string(),
          }),
        )
        .optional(),
    })
    .optional(),
  resources: z.array(
    z.object({
      resource_type: z.string(),
      description: z.string(),
      example: z.string(),
    }),
  ),
});
