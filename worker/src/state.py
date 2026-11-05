from typing import Literal, Optional

from pydantic import BaseModel, Field


class DecisionBrief(BaseModel):
    decision_name: str
    one_liner: str
    problem: str
    capability: str
    current_approach: str
    candidate_approaches: list[str] = Field(default_factory=list)
    deployment_target: str
    hardware_constraints: str
    latency_budget: str
    compliance_constraints: str
    team_context: str
    budget_ceiling: str
    success_metric: str


class CandidateOption(BaseModel):
    name: str
    maturity: str
    license: str
    recency: str
    summary: str
    source: str


class LandscapeIntel(BaseModel):
    candidate_options: list[CandidateOption]
    options_not_considered_but_relevant: list[str]
    category_maturity: Literal["emerging", "consolidating", "mature_commoditized"]
    sources: list[str]


class BenchmarkResult(BaseModel):
    candidate: str
    metric: str
    value: str
    conditions: str
    source: str


class BenchmarkIntel(BaseModel):
    results: list[BenchmarkResult]
    benchmark_coverage_gaps: list[str]
    confidence: Literal["low", "medium", "high"]
    sources: list[str]


class FeasibilityEntry(BaseModel):
    candidate: str
    feasible: bool
    blocking_constraint: str
    notes: str


class InfraConstraintIntel(BaseModel):
    feasibility: list[FeasibilityEntry]
    hardware_fit_summary: str
    compliance_flags: list[str]
    sources: list[str]


class CostEntry(BaseModel):
    candidate: str
    compute_cost_estimate: str
    licensing_cost: str
    ops_burden: str
    total_cost_of_ownership_note: str


class CostModelIntel(BaseModel):
    cost_entries: list[CostEntry]
    cheapest_viable_option: str
    cost_confidence: Literal["low", "medium", "high"]
    sources: list[str]


class IntegrationStrategy(BaseModel):
    recommended_candidates: list[str]
    migration_plan: list[str]
    rollback_plan: str
    monitoring_plan: list[str]
    phased_rollout: str


class ScoreEntry(BaseModel):
    score: int
    justification: str


class AssumptionKillItem(BaseModel):
    assumption: str
    risk_if_wrong: str
    test: str


class NextExperiment(BaseModel):
    experiment: str
    targets_dimension: str
    cost_and_time: str


class TradeoffReport(BaseModel):
    scoring_table: dict[str, ScoreEntry]
    weighted_decision_score: float
    recommended_candidate: str
    assumption_kill_list: list[AssumptionKillItem]
    green_lights: list[str]
    red_flags: list[str]
    next_experiments: list[NextExperiment]
    confidence_rating: Literal["LOW", "MEDIUM", "HIGH"]
    verdict: str
    tattoo_line: str


DeepenTag = Literal["agent_2", "agent_3", "agent_4"]


class EvalState(BaseModel):
    decision_brief: Optional[DecisionBrief] = None
    agent_1_landscape: Optional[LandscapeIntel] = None
    agent_2_benchmark: Optional[BenchmarkIntel] = None
    agent_3_infra_constraint: Optional[InfraConstraintIntel] = None
    agent_4_cost_model: Optional[CostModelIntel] = None
    agent_5_integration_strategy: Optional[IntegrationStrategy] = None
    agent_6_tradeoff_report: Optional[TradeoffReport] = None

    deepen_research: list[DeepenTag] = Field(default_factory=list)
    retry_count: int = 0

    monitoring_enabled: bool = False
