"""
Graph Builder Service.
Builds a NetworkX graph where datasets are nodes and relationships are edges.
Exports graph data for frontend D3.js visualization.
"""

import networkx as nx
from typing import List, Dict
from app.schemas.schemas import (
    DatasetRelationship, RelationshipGraph, GraphNode, GraphEdge, DatasetInfo
)


def build_relationship_graph(
    datasets: Dict[str, DatasetInfo],
    relationships: List[DatasetRelationship],
) -> RelationshipGraph:
    """
    Build a graph from detected relationships.
    Returns serializable graph data for frontend visualization.
    """
    G = nx.Graph()

    # Add nodes (one per dataset)
    nodes: List[GraphNode] = []
    for ds_id, ds_info in datasets.items():
        G.add_node(ds_id, label=ds_info.filename, rows=ds_info.row_count, cols=ds_info.column_count)
        nodes.append(GraphNode(
            id=ds_id,
            label=ds_info.filename,
            row_count=ds_info.row_count,
            column_count=ds_info.column_count,
        ))

    # Add edges (one per relationship, aggregate multiple columns)
    edge_map: Dict[tuple, List[DatasetRelationship]] = {}
    for rel in relationships:
        key = tuple(sorted([rel.source_dataset, rel.target_dataset]))
        if key not in edge_map:
            edge_map[key] = []
        edge_map[key].append(rel)

    edges: List[GraphEdge] = []
    for (src, tgt), rels in edge_map.items():
        best_rel = max(rels, key=lambda r: r.confidence)

        # Build label from column pairs
        col_pairs = [f"{r.source_column}↔{r.target_column}" for r in rels[:3]]
        label = ", ".join(col_pairs)
        if len(rels) > 3:
            label += f" (+{len(rels) - 3} más)"

        G.add_edge(src, tgt, weight=best_rel.confidence, label=label)
        edges.append(GraphEdge(
            source=src,
            target=tgt,
            label=label,
            confidence=best_rel.confidence,
            relationship_type=best_rel.relationship_type.value,
        ))

    return RelationshipGraph(nodes=nodes, edges=edges)
