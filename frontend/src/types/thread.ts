export interface Reference {
  /** Title of the academic reference or paper */
  title: string;
  /** URL link to the academic reference or paper */
  link: string;
  /** Brief description or abstract of the academic reference or paper */
  description: string;
  /** Tag indicating the source of the reference, e.g., 'web', 'scholar' */
  tag: string;
}

export interface Worklet {
  /** Unique identifier for the worklet */
  worklet_id: string;
  /** Title of the project idea */
  title: string;
  /** Problem statement of the project idea (28-33 words) */
  problem_statement: string;
  /** Description of the project idea (providing context/background, max 100 words) */
  description: string;
  /** Specific challenge or use case addressed by the project idea */
  challenge_use_case: string;
  /** Expected deliverables of the project idea */
  deliverables: string;
  /** Key Performance Indicators (KPIs) for the project idea */
  kpis: string[];
  /** Prerequisites for undertaking the project idea */
  prerequisites: string[];
  /** Infrastructure requirements for the project idea */
  infrastructure_requirements: string;
  /** Tentative technology stack for the project idea */
  tech_stack: string;
  /** Milestones for the project idea over a 6-month period */
  milestones: Record<string, any>;
  /** List of relevant academic references or papers for the project idea */
  references: Reference[];
}

export interface Thread {
  thread_id: string;
  thread_name: string;
  custom_prompt?: string;
  links?: string[];
  files?: string[];
  count: number;
  generated: boolean;
  created_at: string;
  worklets?: Worklet[]; // updated to structured worklets
  /** Indicates this thread object was created optimistically on the client and not yet confirmed via GET /thread/{id} */
  local?: boolean;
}

export interface DomainsKeywords {
  domains: {
    worklet: string[];
    link: string[];
    custom_prompt: string[];
    custom: string[];
  };
  keywords: {
    worklet: string[];
    link: string[];
    custom_prompt: string[];
    custom: string[];
  };
}

export interface ProgressMessage {
  message: string;
  timestamp: number;
}
