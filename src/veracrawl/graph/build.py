"""Deterministic basic site graph builder."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphEdgeType,
    GraphFailureType,
    GraphNodeType,
)
from veracrawl.contracts.graph import (
    GraphBuildManifest,
    GraphBuildReport,
    GraphEdge,
    GraphEdgeProvenance,
    GraphNode,
    ProjectionWatermark,
)


@dataclass(frozen=True)
class LinkInput:
    source_url: str
    target_url: str
    provenance_ref: Ref


@dataclass(frozen=True)
class GraphBuildResult:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    provenances: list[GraphEdgeProvenance]
    manifest: GraphBuildManifest | None
    watermark: ProjectionWatermark | None
    report: GraphBuildReport


def build_basic_site_graph(
    *,
    fixture_id: str,
    scenario: str,
    link_inputs: list[LinkInput],
    canonical_inputs: list[LinkInput] | None = None,
    redirect_inputs: list[LinkInput] | None = None,
    page_type_refs: list[Ref] | None = None,
    site_model_refs: list[Ref] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> GraphBuildResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:graph"]
    if scenario == "missing-input" or not _has_inputs(
        link_inputs,
        canonical_inputs,
        redirect_inputs,
        page_type_refs,
        site_model_refs,
    ):
        return _failure_result(
            fixture_id=fixture_id,
            failure=GraphFailureType.MISSING_GRAPH_INPUT,
            policy_refs=policy_refs,
        )
    if scenario == "graph-as-evidence":
        return _failure_result(
            fixture_id=fixture_id,
            failure=GraphFailureType.GRAPH_AS_EVIDENCE,
            policy_refs=policy_refs,
        )

    nodes_by_key: dict[tuple[GraphNodeType, str], GraphNode] = {}
    edges_by_key: dict[tuple[GraphEdgeType, str, str], GraphEdge] = {}
    provenance_inputs: dict[str, list[Ref]] = {}

    def node(node_type: GraphNodeType, key: str, source_ref: Ref) -> GraphNode:
        node_key = (node_type, key)
        if node_key not in nodes_by_key:
            nodes_by_key[node_key] = GraphNode(
                id=f"graph-node:{fixture_id}:{node_type.value}:{stable_hash(key)[:10]}",
                run_ref=f"run:{fixture_id}",
                node_key=key,
                node_type=node_type,
                label=_label_for_key(key),
                source_ref=source_ref,
                property_refs=[f"property:{fixture_id}:{node_type.value}"],
            )
        return nodes_by_key[node_key]

    def edge(
        edge_type: GraphEdgeType,
        source: GraphNode,
        target: GraphNode,
        input_ref: Ref,
    ) -> None:
        edge_key = (edge_type, source.id, target.id)
        edge_hash = stable_hash(edge_key)[:10]
        edge_id = f"graph-edge:{fixture_id}:{edge_type.value}:{edge_hash}"
        if edge_key not in edges_by_key:
            provenance_ref = f"graph-provenance:{fixture_id}:{edge_type.value}:{edge_hash}"
            edges_by_key[edge_key] = GraphEdge(
                id=edge_id,
                run_ref=f"run:{fixture_id}",
                from_node_ref=source.id,
                to_node_ref=target.id,
                edge_type=edge_type,
                provenance_ref=provenance_ref,
                property_refs=[f"property:{fixture_id}:{edge_type.value}"],
            )
            provenance_inputs[edge_id] = []
        provenance_inputs[edge_id].append(input_ref)

    for link in link_inputs:
        source = node(GraphNodeType.URL, link.source_url, link.provenance_ref)
        target = node(GraphNodeType.URL, link.target_url, link.provenance_ref)
        edge(GraphEdgeType.HYPERLINK, source, target, link.provenance_ref)

    for item in redirect_inputs or []:
        source = node(GraphNodeType.URL, item.source_url, item.provenance_ref)
        target = node(GraphNodeType.URL, item.target_url, item.provenance_ref)
        edge(GraphEdgeType.REDIRECT, source, target, item.provenance_ref)

    for item in canonical_inputs or []:
        source = node(GraphNodeType.URL, item.source_url, item.provenance_ref)
        target = node(GraphNodeType.CANONICAL, item.target_url, item.provenance_ref)
        edge(GraphEdgeType.CANONICAL, source, target, item.provenance_ref)

    if page_type_refs or site_model_refs:
        root = node(GraphNodeType.URL, f"https://{fixture_id}.example/", f"site:{fixture_id}")
        for ref in page_type_refs or []:
            page_node = node(GraphNodeType.PAGE_TYPE, ref, ref)
            edge(GraphEdgeType.PAGE_STRUCTURE, root, page_node, ref)
        for ref in site_model_refs or []:
            template_node = node(GraphNodeType.TEMPLATE, ref, ref)
            edge(GraphEdgeType.PAGE_STRUCTURE, root, template_node, ref)

    nodes = sorted(nodes_by_key.values(), key=lambda item: item.id)
    edges = sorted(edges_by_key.values(), key=lambda item: item.id)
    provenances = [
        GraphEdgeProvenance(
            id=edge_item.provenance_ref,
            edge_ref=edge_item.id,
            input_refs=sorted(set(provenance_inputs[edge_item.id])),
            policy_decision_refs=policy_refs,
            evidence_ref_allowed=False,
        )
        for edge_item in edges
    ]
    input_refs = sorted({ref for values in provenance_inputs.values() for ref in values})
    rebuild_hash = stable_hash(
        {
            "nodes": [item.id for item in nodes],
            "edges": [item.id for item in edges],
            "inputs": input_refs,
            "scenario": scenario,
        }
    )
    if scenario == "rebuild-mismatch":
        return _failure_result(
            fixture_id=fixture_id,
            failure=GraphFailureType.REBUILD_MISMATCH,
            policy_refs=policy_refs,
            missing_fields=[GraphFailureType.REBUILD_MISMATCH.value],
        )

    manifest_ref = f"graph-manifest:{fixture_id}"
    watermark = ProjectionWatermark(
        id=f"projection-watermark:{fixture_id}",
        projection_ref=f"graph-projection:{fixture_id}",
        input_manifest_ref=manifest_ref,
        event_cursor_refs=[f"event-cursor:{fixture_id}:graph"],
        rebuild_hash=rebuild_hash,
        freshness_ref=f"freshness:{fixture_id}:graph",
    )
    manifest = GraphBuildManifest(
        id=manifest_ref,
        run_ref=f"run:{fixture_id}",
        input_refs=input_refs,
        graph_version="basic-site-graph:v1",
        node_refs=[item.id for item in nodes],
        edge_refs=[item.id for item in edges],
        provenance_refs=[item.id for item in provenances],
        watermark_ref=watermark.id,
        policy_decision_refs=policy_refs,
        rebuild_hash=rebuild_hash,
    )
    report = GraphBuildReport(
        id=f"graph-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        manifest_ref=manifest.id,
        node_refs=manifest.node_refs,
        edge_refs=manifest.edge_refs,
        provenance_refs=manifest.provenance_refs,
        watermark_ref=watermark.id,
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:graph"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:graph"],
        outbox_refs=[f"outbox:{fixture_id}:graph"],
        operator_status="graph_build_completed",
        completion_result=CompletenessResult.PASS,
    )
    return GraphBuildResult(
        nodes=nodes,
        edges=edges,
        provenances=provenances,
        manifest=manifest,
        watermark=watermark,
        report=report,
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: GraphFailureType,
    policy_refs: list[Ref],
    missing_fields: list[str] | None = None,
) -> GraphBuildResult:
    return GraphBuildResult(
        nodes=[],
        edges=[],
        provenances=[],
        manifest=None,
        watermark=None,
        report=GraphBuildReport(
            id=f"graph-report:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            policy_decision_refs=policy_refs,
            failure_report_refs=[f"graph-failure:{fixture_id}:{failure.value}"],
            missing_ref_fields=missing_fields or [failure.value],
            operator_status=failure.value,
            completion_result=CompletenessResult.FAIL,
        ),
    )


def _has_inputs(
    link_inputs: list[LinkInput],
    canonical_inputs: list[LinkInput] | None,
    redirect_inputs: list[LinkInput] | None,
    page_type_refs: list[Ref] | None,
    site_model_refs: list[Ref] | None,
) -> bool:
    return bool(
        link_inputs
        or canonical_inputs
        or redirect_inputs
        or page_type_refs
        or site_model_refs
    )


def _label_for_key(key: str) -> str:
    parsed = urlparse(key)
    if parsed.netloc:
        return parsed.netloc + parsed.path
    return key
