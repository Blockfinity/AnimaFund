/**
 * Local Agent Worker
 *
 * Runs inference-driven task execution in-process as an async background task.
 * Each worker gets a role-specific system prompt, a subset of tools, and
 * runs a ReAct loop (think → tool_call → observe → repeat → done).
 *
 * This enables multi-agent orchestration on local machines without Conway
 * sandbox infrastructure. Workers share the same Node.js process but run
 * concurrently as independent async tasks.
 */
import type { TaskNode } from "./task-graph.js";
import type { Database } from "better-sqlite3";
import type { ConwayClient } from "../types.js";
interface WorkerInferenceClient {
    chat(params: {
        tier: string;
        messages: any[];
        tools?: any[];
        toolChoice?: string;
        maxTokens?: number;
        temperature?: number;
        responseFormat?: {
            type: string;
        };
    }): Promise<{
        content: string;
        toolCalls?: unknown[];
    }>;
}
interface LocalWorkerConfig {
    db: Database;
    inference: WorkerInferenceClient;
    conway: ConwayClient;
    workerId: string;
    maxTurns?: number;
}
export declare class LocalWorkerPool {
    private readonly config;
    private activeWorkers;
    constructor(config: LocalWorkerConfig);
    /**
     * Spawn a local worker for a task. Returns immediately — the worker
     * runs in the background and reports results via the task graph.
     */
    spawn(task: TaskNode): {
        address: string;
        name: string;
        sandboxId: string;
    };
    getActiveCount(): number;
    /**
     * Check if a worker is currently active in this pool.
     * Accepts either a full address ("local://worker-id") or raw worker ID.
     */
    hasWorker(addressOrId: string): boolean;
    shutdown(): Promise<void>;
    private runWorker;
    private buildWorkerSystemPrompt;
    private buildTaskPrompt;
    private buildWorkerTools;
}
export {};
//# sourceMappingURL=local-worker.d.ts.map