import type { z } from 'zod';
import type {
  ArchitectureOutputSchema,
  ComponentSchema,
  WarningSchema,
} from '../core/schema.js';

export type ArchitectureOutput = z.infer<typeof ArchitectureOutputSchema>;
export type Component = z.infer<typeof ComponentSchema>;
export type Warning = z.infer<typeof WarningSchema>;
