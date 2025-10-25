export class ApiError extends Error {
    status: number;
    code?: number;
    details?: unknown;
    path?: string;
    raw?: unknown;

    constructor(message: string, opts: { status: number; code?: number; details?: unknown; path?: string; raw?: unknown }) {
        super(message);
        this.name = 'ApiError';
        this.status = opts.status;
        this.code = opts.code;
        this.details = opts.details;
        this.path = opts.path;
        this.raw = opts.raw;
    }
}

const isJsonResponse = (res: Response) => {
    const ct = res.headers.get('content-type') || '';
    return ct.includes('application/json') || ct.includes('application/problem+json');
};

async function parseError(res: Response): Promise<ApiError> {
    let body: any = undefined;
    try {
        if (isJsonResponse(res)) {
            body = await res.clone().json();
        } else {
            const text = await res.clone().text();
            if (text) body = { error: { message: text } };
        }
    } catch {
        // ignore parse errors
    }

    const errObj = body?.error ?? body ?? {};
    const message = errObj?.message || `${res.status} ${res.statusText || 'Request failed'}`;
    const code = typeof errObj?.code === 'number' ? errObj.code : undefined;
    const details = errObj?.details;
    const path = errObj?.path;
    return new ApiError(message, { status: res.status, code, details, path, raw: body });
}

/** Ensure response is ok, otherwise throw ApiError with parsed backend payload. */
export async function ensureOk(res: Response): Promise<void> {
    if (!res.ok) {
        throw await parseError(res);
    }
}

/**
 * Perform a fetch returning JSON (when available). Throws ApiError on non-2xx with parsed backend error payload.
 * If the response is not JSON and is 2xx, returns undefined.
 */
export async function requestJson<T = any>(url: string, init?: RequestInit): Promise<T> {
    const res = await fetch(url, init);
    if (!res.ok) {
        throw await parseError(res);
    }
    if (res.status === 204) return undefined as unknown as T;
    if (!isJsonResponse(res)) {
        return undefined as unknown as T;
    }
    return (await res.json()) as T;
}

/**
 * Fetch a binary/blob resource. Throws ApiError on non-2xx with parsed backend error payload.
 */
export async function requestBlob(url: string, init?: RequestInit): Promise<Blob> {
    const res = await fetch(url, init);
    if (!res.ok) {
        throw await parseError(res);
    }
    return await res.blob();
}

/**
 * Helper to pretty print validation details array from backend (FastAPI-like).
 */
export function formatValidationDetails(details: any): string {
    try {
        if (!Array.isArray(details)) return '';
        const lines = details.map((d) => {
            const loc = Array.isArray(d?.loc) ? d.loc.join('.') : String(d?.loc ?? '');
            const msg = d?.msg ?? d?.message ?? 'Invalid value';
            return `- ${loc}: ${msg}`;
        });
        return lines.join('\n');
    } catch {
        return '';
    }
}
