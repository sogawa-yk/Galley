import type { z } from 'zod';
import type {
  DeployStateSchema,
  RmJobRecordSchema,
} from '../core/schema.js';

export type DeployState = z.infer<typeof DeployStateSchema>;
export type RmJobRecord = z.infer<typeof RmJobRecordSchema>;
