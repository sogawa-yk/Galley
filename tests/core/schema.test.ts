import { describe, it, expect } from 'vitest';
import {
  SessionSchema,
  HearingResultSchema,
  ArchitectureOutputSchema,
  CreateSessionArgsSchema,
  SaveAnswerArgsSchema,
  SaveAnswersBatchArgsSchema,
  SaveArchitectureArgsSchema,
  ExportMermaidArgsSchema,
  ExportIacArgsSchema,
  ExportAllArgsSchema,
  HearingQuestionsConfigSchema,
  HearingFlowConfigSchema,
  OciServicesConfigSchema,
  OciArchitecturesConfigSchema,
  OciTerraformConfigSchema,
} from '../../src/core/schema.js';

const VALID_UUID = '550e8400-e29b-41d4-a716-446655440000';
const VALID_DATETIME = '2026-01-01T00:00:00Z';

describe('SessionSchema', () => {
  it('should validate a valid session', () => {
    const result = SessionSchema.safeParse({
      session_id: VALID_UUID,
      created_at: VALID_DATETIME,
      updated_at: VALID_DATETIME,
      status: 'in_progress',
      project_description: 'Test project',
    });
    expect(result.success).toBe(true);
  });

  it('should reject invalid UUID', () => {
    const result = SessionSchema.safeParse({
      session_id: 'not-a-uuid',
      created_at: VALID_DATETIME,
      updated_at: VALID_DATETIME,
      status: 'in_progress',
      project_description: 'Test',
    });
    expect(result.success).toBe(false);
  });

  it('should reject invalid status', () => {
    const result = SessionSchema.safeParse({
      session_id: VALID_UUID,
      created_at: VALID_DATETIME,
      updated_at: VALID_DATETIME,
      status: 'unknown',
      project_description: 'Test',
    });
    expect(result.success).toBe(false);
  });
});

describe('HearingResultSchema', () => {
  const minimalHearingResult = {
    metadata: {
      hearing_id: VALID_UUID,
      created_at: VALID_DATETIME,
      version: '1.0.0' as const,
      status: 'in_progress' as const,
    },
    project_overview: {
      description: 'Test project',
    },
    requirements: {},
  };

  it('should validate minimal hearing result (in-progress)', () => {
    const result = HearingResultSchema.safeParse(minimalHearingResult);
    expect(result.success).toBe(true);
  });

  it('should validate hearing result with partial answers', () => {
    const result = HearingResultSchema.safeParse({
      ...minimalHearingResult,
      requirements: {
        scale: {
          concurrent_users: {
            value: '1000',
            source: 'user_selected',
          },
        },
      },
    });
    expect(result.success).toBe(true);
  });

  it('should validate hearing result with estimation', () => {
    const result = HearingResultSchema.safeParse({
      ...minimalHearingResult,
      requirements: {
        scale: {
          concurrent_users: {
            value: 5000,
            source: 'estimated',
            estimation: {
              confidence_label: 'general_estimate',
              reasoning: 'Based on industry average',
            },
          },
        },
      },
    });
    expect(result.success).toBe(true);
  });

  it('should reject invalid version', () => {
    const result = HearingResultSchema.safeParse({
      ...minimalHearingResult,
      metadata: { ...minimalHearingResult.metadata, version: '2.0.0' },
    });
    expect(result.success).toBe(false);
  });

  it('should reject missing description', () => {
    const result = HearingResultSchema.safeParse({
      ...minimalHearingResult,
      project_overview: {},
    });
    expect(result.success).toBe(false);
  });
});

describe('ArchitectureOutputSchema', () => {
  it('should validate a valid architecture output', () => {
    const result = ArchitectureOutputSchema.safeParse({
      session_id: VALID_UUID,
      components: [
        {
          category: 'compute',
          service_name: 'OKE',
          purpose: 'Container orchestration',
          reason: 'Scalable container management',
        },
      ],
      decisions: [
        {
          category: 'compute',
          decision: 'Use OKE for containers',
          reason: 'Better scalability',
        },
      ],
      warnings: [
        {
          type: 'cost',
          message: 'Consider Reserved pricing',
          severity: 'info',
        },
      ],
    });
    expect(result.success).toBe(true);
  });

  it('should reject invalid severity', () => {
    const result = ArchitectureOutputSchema.safeParse({
      session_id: VALID_UUID,
      components: [],
      decisions: [],
      warnings: [{ type: 'x', message: 'y', severity: 'critical' }],
    });
    expect(result.success).toBe(false);
  });
});

describe('Tool Args Schemas', () => {
  describe('CreateSessionArgsSchema', () => {
    it('should validate valid args', () => {
      const result = CreateSessionArgsSchema.safeParse({
        project_description: 'A new web app project',
      });
      expect(result.success).toBe(true);
    });

    it('should reject empty description', () => {
      const result = CreateSessionArgsSchema.safeParse({
        project_description: '',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('SaveAnswerArgsSchema', () => {
    it('should validate with string value', () => {
      const result = SaveAnswerArgsSchema.safeParse({
        session_id: VALID_UUID,
        question_id: 'concurrent_users',
        category: 'scale',
        value: '1000',
        source: 'user_selected',
      });
      expect(result.success).toBe(true);
    });

    it('should validate with numeric value and estimation', () => {
      const result = SaveAnswerArgsSchema.safeParse({
        session_id: VALID_UUID,
        question_id: 'concurrent_users',
        category: 'scale',
        value: 5000,
        source: 'estimated',
        estimation: {
          confidence_label: 'general_estimate',
          reasoning: 'Based on industry data',
        },
      });
      expect(result.success).toBe(true);
    });

    it('should reject invalid source', () => {
      const result = SaveAnswerArgsSchema.safeParse({
        session_id: VALID_UUID,
        question_id: 'x',
        category: 'y',
        value: 'z',
        source: 'invalid_source',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('SaveAnswersBatchArgsSchema', () => {
    it('should validate batch answers', () => {
      const result = SaveAnswersBatchArgsSchema.safeParse({
        session_id: VALID_UUID,
        answers: [
          { question_id: 'q1', category: 'scale', value: '100', source: 'user_selected' },
          { question_id: 'q2', category: 'traffic', value: true, source: 'user_free_text' },
        ],
      });
      expect(result.success).toBe(true);
    });
  });

  describe('SaveArchitectureArgsSchema', () => {
    it('should default warnings to empty array', () => {
      const result = SaveArchitectureArgsSchema.safeParse({
        session_id: VALID_UUID,
        components: [],
        decisions: [],
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.warnings).toEqual([]);
      }
    });
  });

  describe('ExportMermaidArgsSchema', () => {
    it('should reject empty mermaid code', () => {
      const result = ExportMermaidArgsSchema.safeParse({
        session_id: VALID_UUID,
        mermaid_code: '',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('ExportIacArgsSchema', () => {
    it('should reject empty files array', () => {
      const result = ExportIacArgsSchema.safeParse({
        session_id: VALID_UUID,
        files: [],
      });
      expect(result.success).toBe(false);
    });
  });

  describe('ExportAllArgsSchema', () => {
    it('should validate with optional fields', () => {
      const result = ExportAllArgsSchema.safeParse({
        session_id: VALID_UUID,
      });
      expect(result.success).toBe(true);
    });

    it('should validate with all fields', () => {
      const result = ExportAllArgsSchema.safeParse({
        session_id: VALID_UUID,
        mermaid_code: 'graph TD\n  A --> B',
        iac_files: [{ name: 'main.tf', content: 'resource {}' }],
      });
      expect(result.success).toBe(true);
    });
  });
});

describe('Config Schemas', () => {
  describe('HearingQuestionsConfigSchema', () => {
    it('should validate valid config', () => {
      const result = HearingQuestionsConfigSchema.safeParse({
        version: '1.0.0',
        categories: [
          { id: 'scale', label: '規模', required: true, description: 'ユーザー数' },
        ],
      });
      expect(result.success).toBe(true);
    });

    it('should default required to true', () => {
      const result = HearingQuestionsConfigSchema.safeParse({
        version: '1.0.0',
        categories: [{ id: 'scale', label: '規模' }],
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.categories[0]?.required).toBe(true);
      }
    });
  });

  describe('HearingFlowConfigSchema', () => {
    it('should validate valid flow config', () => {
      const result = HearingFlowConfigSchema.safeParse({
        version: '1.0.0',
        default_order: ['scale', 'traffic'],
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.conditional_rules).toEqual([]);
      }
    });
  });

  describe('OciServicesConfigSchema', () => {
    it('should validate valid services config', () => {
      const result = OciServicesConfigSchema.safeParse({
        version: '1.0.0',
        services: [
          {
            name: 'Compute',
            category: 'コンピュート',
            description: '仮想マシン',
            use_cases: ['Webサーバー'],
          },
        ],
      });
      expect(result.success).toBe(true);
    });
  });

  describe('OciArchitecturesConfigSchema', () => {
    it('should validate valid architectures config', () => {
      const result = OciArchitecturesConfigSchema.safeParse({
        version: '1.0.0',
        patterns: [
          {
            id: 'web_three_tier',
            name: 'Web三層',
            description: '基本構成',
            components: ['LB', 'Compute', 'DB'],
          },
        ],
      });
      expect(result.success).toBe(true);
    });
  });

  describe('OciTerraformConfigSchema', () => {
    it('should validate valid terraform config', () => {
      const result = OciTerraformConfigSchema.safeParse({
        version: '1.0.0',
        resources: [
          {
            resource_type: 'oci_core_vcn',
            description: 'VCN',
            example: 'resource "oci_core_vcn" "main" {}',
          },
        ],
      });
      expect(result.success).toBe(true);
    });
  });
});
