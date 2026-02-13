import type { z } from 'zod';
import type {
  AnsweredItemSchema,
  EstimationSchema,
  HearingResultSchema,
} from '../core/schema.js';

export type Estimation = z.infer<typeof EstimationSchema>;
export type AnsweredItem = z.infer<typeof AnsweredItemSchema>;
export type HearingResult = z.infer<typeof HearingResultSchema>;
export type ConfidenceLabel = Estimation['confidence_label'];
export type AnswerSource = AnsweredItem['source'];
