import type { Goal, TaskNode } from "./task-graph.js";
import { UnifiedInferenceClient } from "../inference/inference-client.js";
export interface PlannerOutput {
    analysis: string;
    strategy: string;
    customRoles: CustomRoleDef[];
    tasks: PlannedTask[];
    risks: string[];
    estimatedTotalCostCents: number;
    estimatedTimeMinutes: number;
}
export interface CustomRoleDef {
    name: string;
    description: string;
    systemPrompt: string;
    allowedTools: string[];
    deniedTools?: string[];
    model: string;
    maxTokensPerTurn?: number;
    maxTurnsPerTask?: number;
    treasuryLimits?: {
        maxSingleTransfer: number;
        maxDailySpend: number;
    };
    rationale: string;
}
export interface PlannedTask {
    title: string;
    description: string;
    agentRole: string;
    dependencies: number[];
    estimatedCostCents: number;
    priority: number;
    timeoutMs: number;
}
export interface PlannerContext {
    creditsCents: number;
    usdcBalance: number;
    survivalTier: string;
    availableRoles: string[];
    customRoles: string[];
    activeGoals: any[];
    recentOutcomes: any[];
    marketIntel: string;
    idleAgents: number;
    busyAgents: number;
    maxAgents: number;
    workspaceFiles: string[];
}
export declare function planGoal(goal: Goal, context: PlannerContext, inference: UnifiedInferenceClient): Promise<PlannerOutput>;
export declare function replanAfterFailure(goal: Goal, failedTask: TaskNode, context: PlannerContext, inference: UnifiedInferenceClient): Promise<PlannerOutput>;
export declare function buildPlannerPrompt(context: PlannerContext): string;
export declare function validatePlannerOutput(output: unknown): PlannerOutput;
//# sourceMappingURL=planner.d.ts.map