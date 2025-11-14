import {
    ArrayAttribute,
    ObjectAttribute,
    StringAttribute,
    Thread,
    ThreadApiResponse,
    TransformedWorklet,
    WorkletPayload,
} from '@/types/thread';

const isRecord = (value: unknown): value is Record<string, unknown> => {
    return !!value && typeof value === 'object' && !Array.isArray(value);
};

const clampIndex = (index: number, length: number): number => {
    if (length <= 0) return 0;
    if (Number.isNaN(index)) return 0;
    return Math.min(Math.max(index, 0), length - 1);
};

const sanitizeStringIterations = (iterations: unknown): string[] => {
    if (!Array.isArray(iterations)) {
        return [];
    }
    return iterations.map((value) => {
        if (typeof value === 'string') return value;
        return value != null ? String(value) : '';
    });
};

const sanitizeArrayIterations = (iterations: unknown): string[][] => {
    if (!Array.isArray(iterations)) {
        return [];
    }
    return iterations.map((entry) => {
        if (!Array.isArray(entry)) {
            return [];
        }
        return entry.map((value) => {
            if (typeof value === 'string') return value;
            return value != null ? String(value) : '';
        });
    });
};

const sanitizeObjectIterations = (iterations: unknown): Record<string, unknown>[] => {
    if (!Array.isArray(iterations)) {
        return [];
    }
    return iterations.map((entry) => (isRecord(entry) ? { ...entry } : {}));
};

const normalizeStringAttribute = (attr?: Partial<StringAttribute>): StringAttribute => {
    const sanitizedIterations = sanitizeStringIterations(attr?.iterations);
    const iterations = sanitizedIterations.length > 0 ? sanitizedIterations : [''];
    const selected_index = clampIndex(attr?.selected_index ?? 0, iterations.length);
    return {
        selected_index,
        iterations,
    };
};

const normalizeArrayAttribute = (attr?: Partial<ArrayAttribute>): ArrayAttribute => {
    const sanitizedIterations = sanitizeArrayIterations(attr?.iterations);
    const iterations = sanitizedIterations.length > 0 ? sanitizedIterations : [[]];
    const selected_index = clampIndex(attr?.selected_index ?? 0, iterations.length);
    return {
        selected_index,
        iterations,
    };
};

const normalizeObjectAttribute = (attr?: Partial<ObjectAttribute>): ObjectAttribute => {
    const sanitizedIterations = sanitizeObjectIterations(attr?.iterations);
    const iterations = sanitizedIterations.length > 0 ? sanitizedIterations : [{}];
    const selected_index = clampIndex(attr?.selected_index ?? 0, iterations.length);
    return {
        selected_index,
        iterations,
    };
};

const isTransformedWorklet = (value: WorkletPayload): value is TransformedWorklet => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
        return false;
    }
    return 'title' in value && typeof (value as TransformedWorklet).title === 'object';
};

const wrapString = (value: unknown): StringAttribute => {
    const normalized = typeof value === 'string' ? value : value != null ? String(value) : '';
    return {
        selected_index: 0,
        iterations: [normalized],
    };
};

const wrapArray = (value: unknown): ArrayAttribute => {
    const list = Array.isArray(value) ? value : [];
    const normalized = list.map((item) => {
        if (typeof item === 'string') return item;
        return item != null ? String(item) : '';
    });
    return {
        selected_index: 0,
        iterations: [normalized],
    };
};

const wrapObject = (value: unknown): ObjectAttribute => {
    const normalized = isRecord(value) ? value : {};
    return {
        selected_index: 0,
        iterations: [{ ...normalized }],
    };
};
export const ensureTransformedWorklet = (input: WorkletPayload): TransformedWorklet => {
    if (isTransformedWorklet(input)) {
        return {
            worklet_id: input.worklet_id,
            title: normalizeStringAttribute(input.title),
            problem_statement: normalizeStringAttribute(input.problem_statement),
            description: normalizeStringAttribute(input.description),
            reasoning: typeof input.reasoning === 'string' ? input.reasoning : '',
            challenge_use_case: normalizeStringAttribute(input.challenge_use_case),
            deliverables: normalizeStringAttribute(input.deliverables),
            kpis: normalizeArrayAttribute(input.kpis),
            prerequisites: normalizeArrayAttribute(input.prerequisites),
            infrastructure_requirements: normalizeStringAttribute(input.infrastructure_requirements),
            tech_stack: normalizeStringAttribute(input.tech_stack),
            milestones: normalizeObjectAttribute(input.milestones),
            references: Array.isArray(input.references) ? input.references : [],
        };
    }

    const legacy = input as any;

    return {
        worklet_id: legacy.worklet_id,
        title: wrapString(legacy.title),
        problem_statement: wrapString(legacy.problem_statement),
        description: wrapString(legacy.description),
        reasoning: typeof legacy.reasoning === 'string' ? legacy.reasoning : '',
        challenge_use_case: wrapString(legacy.challenge_use_case),
        deliverables: wrapString(legacy.deliverables),
        kpis: wrapArray(legacy.kpis),
        prerequisites: wrapArray(legacy.prerequisites),
        infrastructure_requirements: wrapString(legacy.infrastructure_requirements),
        tech_stack: wrapString(legacy.tech_stack),
        milestones: wrapObject(legacy.milestones),
        references: Array.isArray(legacy.references) ? legacy.references : [],
    };
};

export const normalizeThreadResponse = (thread: ThreadApiResponse): Thread => {
    const { worklets, ...rest } = thread;
    const normalizedWorklets = Array.isArray(worklets) ? worklets.map(ensureTransformedWorklet) : [];
    const base = { ...(rest as Record<string, unknown>) };
    if (typeof base.cluster_id !== 'string') {
        base.cluster_id = '';
    }
    return {
        ...(base as Omit<Thread, 'worklets'>),
        worklets: normalizedWorklets,
    };
};

const selectFromIterations = <T>(attr: { iterations: T[]; selected_index: number } | undefined, index?: number): T | undefined => {
    if (!attr) return undefined;
    const iterations = Array.isArray(attr.iterations) ? attr.iterations : [];
    if (iterations.length === 0) return undefined;
    const target = typeof index === 'number' ? clampIndex(index, iterations.length) : clampIndex(attr.selected_index ?? 0, iterations.length);
    return iterations[target];
};

export const getStringIteration = (attr?: StringAttribute, index?: number): string => {
    const value = selectFromIterations<string>(attr as any, index);
    return typeof value === 'string' ? value : '';
};

export const getArrayIteration = (attr?: ArrayAttribute, index?: number): string[] => {
    const value = selectFromIterations<string[]>(attr as any, index);
    return Array.isArray(value) ? value.map((item) => (typeof item === 'string' ? item : item != null ? String(item) : '')).filter(Boolean) : [];
};

export const getObjectIteration = (attr?: ObjectAttribute, index?: number): Record<string, unknown> => {
    const value = selectFromIterations<Record<string, unknown>>(attr as any, index);
    return isRecord(value) ? value : {};
};

export const getIterationCount = (attr?: { iterations: unknown[] }): number => {
    return Array.isArray(attr?.iterations) ? attr!.iterations.length : 0;
};

export const getSelectedIndex = (attr?: { selected_index: number }): number => {
    return typeof attr?.selected_index === 'number' ? attr.selected_index : 0;
};

export const clampToIterations = (attr: { iterations: unknown[] }, index: number): number => {
    const length = Array.isArray(attr.iterations) ? attr.iterations.length : 0;
    return clampIndex(index, length);
};
