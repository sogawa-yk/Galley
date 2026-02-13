import type { z } from 'zod';
import type { SessionSchema } from '../core/schema.js';

export type Session = z.infer<typeof SessionSchema>;
export type SessionStatus = Session['status'];

export interface SessionSummary {
  session_id: string;
  project_description: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
}
