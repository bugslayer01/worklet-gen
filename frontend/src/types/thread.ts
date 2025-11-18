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

export interface StringAttribute {
  /** Index pointing at the selected iteration */
  selected_index: number;
  /** All candidate iterations for this attribute */
  iterations: string[];
}

export interface ArrayAttribute {
  /** Index pointing at the selected iteration */
  selected_index: number;
  /** All candidate iterations for this attribute */
  iterations: string[][];
}

export interface ObjectAttribute {
  /** Index pointing at the selected iteration */
  selected_index: number;
  /** All candidate iterations for this attribute */
  iterations: Record<string, unknown>[];
}

export interface TransformedWorklet {
  /** Unique identifier for the worklet */
  worklet_id: string;
  /** Transformed title attribute */
  title: StringAttribute;
  /** Transformed problem statement attribute */
  problem_statement: StringAttribute;
  /** Transformed description attribute */
  description: StringAttribute;
  /** LLM's rationale for why this worklet was proposed */
  reasoning: string;
  /** Transformed challenge use case attribute */
  challenge_use_case: StringAttribute;
  /** Transformed deliverables attribute */
  deliverables: ArrayAttribute;
  /** Transformed KPIs attribute */
  kpis: ArrayAttribute;
  /** Transformed prerequisites attribute */
  prerequisites: ArrayAttribute;
  /** Transformed infrastructure requirements attribute */
  infrastructure_requirements: StringAttribute;
  /** Transformed tech stack attribute */
  tech_stack: StringAttribute;
  /** Transformed milestones attribute */
  milestones: ObjectAttribute;
  /** List of relevant academic references or papers for the project idea */
  references: Reference[];
}

export interface WorkletIteration extends TransformedWorklet {
  /** Unique identifier for this worklet iteration */
  iteration_id: string;
  /** Creation timestamp for this iteration */
  created_at: string;
}

export interface WorkletWithIterations {
  /** Unique identifier for the worklet */
  worklet_id: string;
  /** Index of the default worklet iteration */
  selected_iteration_index: number;
  /** All iterations available for this worklet */
  iterations: WorkletIteration[];
}

export interface Worklet {
  /** Unique identifier for the worklet */
  worklet_id: string;
  /** Title of the project idea */
  title: string;
  /** Problem statement of the project idea (min 50 words) */
  problem_statement: string;
  /** Description of the project idea (providing context/background, max 100 words) */
  description: string;
  /** LLM's rationale for why this worklet was proposed */
  reasoning: string;
  /** Specific challenge or use case addressed by the project idea */
  challenge_use_case: string;
  /** Expected deliverables of the project idea */
  deliverables: string[];
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

export type WorkletPayload = Worklet | TransformedWorklet | WorkletWithIterations;

export type WorkletFieldKey =
  | 'title'
  | 'problem_statement'
  | 'description'
  | 'challenge_use_case'
  | 'deliverables'
  | 'kpis'
  | 'prerequisites'
  | 'infrastructure_requirements'
  | 'tech_stack'
  | 'milestones';

export interface SelectIterationResponse {
  success: boolean;
  worklet_id: string;
  field: WorkletFieldKey;
  selected_index: number;
}

export interface IterateWorkletResponse {
  worklet_id: string;
  worklet_iteration_id: string;
  field: WorkletFieldKey;
  selected_index: number;
  iterations: unknown[];
}

export interface EnhanceWorkletResponse {
  worklet_id: string;
  selected_iteration_index: number;
  iteration: unknown;
}

export interface SelectWorkletIterationResponse {
  success: boolean;
  worklet_id: string;
  selected_iteration_index: number;
}

export interface Thread {
  thread_id: string;
  thread_name: string;
  cluster_id: string;
  custom_prompt?: string;
  links?: string[];
  files?: string[];
  count: number;
  generated: boolean;
  created_at: string;
  worklets?: WorkletWithIterations[];
  /** Indicates this thread object was created optimistically on the client and not yet confirmed via GET /thread/{id} */
  local?: boolean;
}

export type ThreadApiResponse = Omit<Thread, 'worklets'> & {
  worklets?: unknown[];
};

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
