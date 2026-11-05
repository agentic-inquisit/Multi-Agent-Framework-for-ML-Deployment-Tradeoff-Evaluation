from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from .agents.benchmark import benchmark_node
from .agents.cost_modeling import cost_modeling_node
from .agents.infra_constraint import infra_constraint_node
from .agents.integration_strategist import integration_strategist_node
from .agents.landscape import landscape_node
from .agents.synthesis import route_after_synthesis, synthesis_node
from .orchestrator import orchestrator_node
from .state import EvalState


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    builder = StateGraph(EvalState)

    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("agent_1_landscape", landscape_node)
    builder.add_node("agent_2_benchmark", benchmark_node)
    builder.add_node("agent_3_infra_constraint", infra_constraint_node)
    builder.add_node("agent_4_cost_model", cost_modeling_node)
    builder.add_node("agent_5_integration", integration_strategist_node)
    builder.add_node("agent_6_synthesis", synthesis_node)

    builder.add_edge(START, "orchestrator")
    builder.add_edge("orchestrator", "agent_1_landscape")

    # agent_1_landscape runs alone first so 2-4 always see its expanded
    # candidate list, same rationale as the original build-strategist join.
    builder.add_edge("agent_1_landscape", "agent_2_benchmark")
    builder.add_edge("agent_1_landscape", "agent_3_infra_constraint")
    builder.add_edge("agent_1_landscape", "agent_4_cost_model")

    builder.add_edge("agent_2_benchmark", "agent_5_integration")
    builder.add_edge("agent_3_infra_constraint", "agent_5_integration")
    builder.add_edge("agent_4_cost_model", "agent_5_integration")

    builder.add_edge("agent_5_integration", "agent_6_synthesis")
    builder.add_conditional_edges("agent_6_synthesis", route_after_synthesis, [
        "agent_2_benchmark",
        "agent_3_infra_constraint",
        "agent_4_cost_model",
        END,
    ])

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
