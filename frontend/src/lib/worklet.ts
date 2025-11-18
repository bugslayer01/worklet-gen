import {
    ArrayAttribute,
    ObjectAttribute,
    StringAttribute,
    Thread,
    ThreadApiResponse,
    TransformedWorklet,
    WorkletIteration,
    WorkletPayload,
    WorkletWithIterations,
} from '@/types/thread';

const TEXT_LIST_SPLIT_REGEX = /[\r\n]+|\s*[;\u2022]\s*/u;

const isRecord = (value: unknown): value is Record<string, unknown> => {
    return !!value && typeof value === 'object' && !Array.isArray(value);
};

const clampIndex = (index: number, length: number): number => {
    if (length <= 0) {
        return 0;
    }
    const numericIndex = Number.isFinite(index) ? Math.trunc(index) : 0;
    return Math.min(Math.max(numericIndex, 0), length - 1);
};

const generateIterationId = (): string => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }
    return `iter-${Math.random().toString(36).slice(2, 10)}`;
};

const sanitizeStringIterations = (iterations: unknown): string[] => {
    if (!Array.isArray(iterations)) {
        return [];
    }
    return iterations.map((value) => {
        if (typeof value === 'string') {
            return value;
        }
        if (value == null) {
            return '';
        }
        return String(value);
    });
};

const normalizeTextList = (input: unknown): string[] => {
    if (Array.isArray(input)) {
        return input
            .map((value) => (typeof value === 'string' ? value : value != null ? String(value) : ''))
            .map((value) => value.trim())
            .filter((value) => value.length > 0);
    }

    if (input == null) {
        return [];
    }

    const text = String(input).trim();
    if (text.length === 0) {
        return [];
    }

    return text
        .split(TEXT_LIST_SPLIT_REGEX)
        .map((value) => value.trim())
        .filter((value) => value.length > 0);
};

const sanitizeArrayIterations = (iterations: unknown): string[][] => {
    if (!Array.isArray(iterations)) {
        return [];
    }
    return iterations.map((entry) => normalizeTextList(entry));
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
    if (!isRecord(value)) {
        return false;
    }
    return (
        'title' in value &&
        isRecord((value as TransformedWorklet).title) &&
        Array.isArray((value as TransformedWorklet).title.iterations)
    );
};

const wrapString = (value: unknown): StringAttribute => {
    const normalized = typeof value === 'string' ? value : value != null ? String(value) : '';
    return {
        selected_index: 0,
        iterations: [normalized],
    };
};

const wrapArray = (value: unknown): ArrayAttribute => {
    const normalized = normalizeTextList(value);
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
            deliverables: normalizeArrayAttribute(input.deliverables),
            kpis: normalizeArrayAttribute(input.kpis),
            prerequisites: normalizeArrayAttribute(input.prerequisites),
            infrastructure_requirements: normalizeStringAttribute(input.infrastructure_requirements),
            tech_stack: normalizeStringAttribute(input.tech_stack),
            milestones: normalizeObjectAttribute(input.milestones),
            references: Array.isArray(input.references) ? input.references : [],
        };
    }

    const legacy = input as unknown as Record<string, unknown>;

    return {
        worklet_id: typeof legacy.worklet_id === 'string' ? legacy.worklet_id : '',
        title: wrapString(legacy.title),
        problem_statement: wrapString(legacy.problem_statement),
        description: wrapString(legacy.description),
        reasoning: typeof legacy.reasoning === 'string' ? legacy.reasoning : '',
        challenge_use_case: wrapString(legacy.challenge_use_case),
        deliverables: wrapArray(legacy.deliverables),
        kpis: wrapArray(legacy.kpis),
        prerequisites: wrapArray(legacy.prerequisites),
        infrastructure_requirements: wrapString(legacy.infrastructure_requirements),
        tech_stack: wrapString(legacy.tech_stack),
        milestones: wrapObject(legacy.milestones),
        references: Array.isArray(legacy.references) ? legacy.references : [],
    };
};

const ensureWorkletIterationInternal = (
    input: WorkletPayload | WorkletIteration,
): WorkletIteration => {
    const normalized = ensureTransformedWorklet(input as WorkletPayload);
    const record = isRecord(input) ? input : {};
    const iterationIdRaw = (record as Record<string, unknown>).iteration_id;
    const createdAtRaw = (record as Record<string, unknown>).created_at;

    const iteration_id =
        typeof iterationIdRaw === 'string' && iterationIdRaw.trim().length > 0
            ? iterationIdRaw
            : generateIterationId();
    const created_at =
        typeof createdAtRaw === 'string' && createdAtRaw.trim().length > 0
            ? createdAtRaw
            : new Date().toISOString();

    return {
        ...normalized,
        iteration_id,
        created_at,
    };
};

export const ensureWorkletIteration = (
    input: WorkletPayload | WorkletIteration,
): WorkletIteration => ensureWorkletIterationInternal(input);

const isWorkletBundle = (value: unknown): value is WorkletWithIterations => {
    if (!isRecord(value)) {
        return false;
    }
    const candidate = value as Record<string, unknown>;
    const iterations = candidate.iterations;
    const selectedIndex = candidate.selected_iteration_index;
    const workletId = candidate.worklet_id;

    return (
        Array.isArray(iterations) &&
        typeof selectedIndex === 'number' &&
        typeof workletId === 'string'
    );
};

export const ensureWorkletBundle = (
    input: WorkletPayload | WorkletWithIterations,
): WorkletWithIterations => {
    if (isWorkletBundle(input)) {
        const iterationsSource = Array.isArray(input.iterations) ? input.iterations : [];
        const iterations = iterationsSource.map((iteration) =>
            ensureWorkletIterationInternal(iteration as WorkletIteration),
        );
        const safeIterations =
            iterations.length > 0
                ? iterations
                : [ensureWorkletIterationInternal(input as WorkletPayload)];
        const selected = clampIndex(
            typeof input.selected_iteration_index === 'number'
                ? input.selected_iteration_index
                : 0,
            safeIterations.length,
        );
        const workletId =
            typeof input.worklet_id === 'string' && input.worklet_id.trim().length > 0
                ? input.worklet_id
                : safeIterations[0]?.worklet_id ?? '';
        return {
            worklet_id: workletId,
            selected_iteration_index: selected,
            iterations: safeIterations,
        };
    }

    const iteration = ensureWorkletIterationInternal(input as WorkletPayload);
    return {
        worklet_id: iteration.worklet_id,
        selected_iteration_index: 0,
        iterations: [iteration],
    };
};

export const normalizeThreadResponse = (thread: ThreadApiResponse): Thread => {
    const { worklets, ...rest } = thread;
    const normalizedWorklets = Array.isArray(worklets)
        ? worklets.map((entry) => ensureWorkletBundle(entry as WorkletPayload))
        : [];
    const base = { ...(rest as Record<string, unknown>) };

    if (typeof base.thread_id !== 'string') {
        base.thread_id = '';
    }
    if (typeof base.thread_name !== 'string') {
        base.thread_name = '';
    }
    if (typeof base.cluster_id !== 'string') {
        base.cluster_id = '';
    }
    if (typeof base.custom_prompt !== 'string' && base.custom_prompt !== undefined) {
        base.custom_prompt = String(base.custom_prompt);
    }
    if (!Array.isArray(base.links)) {
        base.links = [];
    }
    if (!Array.isArray(base.files)) {
        base.files = [];
    }
    if (typeof base.count !== 'number') {
        base.count = 0;
    }
    if (typeof base.generated !== 'boolean') {
        base.generated = false;
    }
    if (typeof base.created_at !== 'string') {
        base.created_at = new Date().toISOString();
    }

    return {
        ...(base as Omit<Thread, 'worklets'>),
        worklets: normalizedWorklets,
    };
};

const selectFromIterations = <T>(
    attr: { iterations: T[]; selected_index: number } | undefined,
    index?: number,
): T | undefined => {
    if (!attr) {
        return undefined;
    }
    const iterations = Array.isArray(attr.iterations) ? attr.iterations : [];
    if (iterations.length === 0) {
        return undefined;
    }
    const target =
        typeof index === 'number'
            ? clampIndex(index, iterations.length)
            : clampIndex(attr.selected_index ?? 0, iterations.length);
    return iterations[target];
};

export const getStringIteration = (attr?: StringAttribute, index?: number): string => {
    const value = selectFromIterations<string>(attr, index);
    return typeof value === 'string' ? value : '';
};

export const getArrayIteration = (attr?: ArrayAttribute, index?: number): string[] => {
    const value = selectFromIterations<string[]>(attr, index);
    return Array.isArray(value)
        ? value
            .map((item) =>
                typeof item === 'string' ? item : item != null ? String(item) : '',
            )
            .filter((item) => item.length > 0)
        : [];
};

export const getObjectIteration = (
    attr?: ObjectAttribute,
    index?: number,
): Record<string, unknown> => {
    const value = selectFromIterations<Record<string, unknown>>(attr, index);
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

export const clampWorkletIterationIndex = (
    worklet: WorkletWithIterations,
    index: number,
): number => clampIndex(index, worklet.iterations.length);

export const getWorkletIterationAt = (
    worklet: WorkletWithIterations,
    index?: number,
): WorkletIteration => {
    const iterations = Array.isArray(worklet.iterations) ? worklet.iterations : [];
    if (iterations.length === 0) {
        return ensureWorkletIteration(worklet as unknown as WorkletPayload);
    }
    const resolvedIndex =
        typeof index === 'number'
            ? clampIndex(index, iterations.length)
            : clampIndex(worklet.selected_iteration_index ?? 0, iterations.length);
    return iterations[resolvedIndex];
};

export const getWorkletIterationCount = (worklet: WorkletWithIterations): number => {
    return worklet.iterations.length;
};

export const getDefaultWorkletIteration = (
    worklet: WorkletWithIterations,
): WorkletIteration => getWorkletIterationAt(worklet, worklet.selected_iteration_index);
