"""
Dataset Matcher Service.
Finds relationships between datasets using:
- Column name matching
- Semantic similarity of column names
- Data type compatibility
- Value overlap analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Set
from difflib import SequenceMatcher
from app.schemas.schemas import DatasetRelationship, RelationshipType


def find_relationships(
    datasets: Dict[str, pd.DataFrame],
    dataset_names: Dict[str, str],
) -> List[DatasetRelationship]:
    """
    Find all possible relationships between datasets.
    Returns list of detected relationships with confidence scores.
    """
    relationships: List[DatasetRelationship] = []
    dataset_ids = list(datasets.keys())

    for i in range(len(dataset_ids)):
        for j in range(i + 1, len(dataset_ids)):
            id_a = dataset_ids[i]
            id_b = dataset_ids[j]
            df_a = datasets[id_a]
            df_b = datasets[id_b]

            # 1. Exact column name matches
            name_matches = _find_name_matches(id_a, id_b, df_a, df_b)
            relationships.extend(name_matches)

            # 2. Semantic column name similarity
            semantic_matches = _find_semantic_matches(id_a, id_b, df_a, df_b)
            # Avoid duplicates with name matches
            existing_pairs = {(r.source_column, r.target_column) for r in name_matches}
            for m in semantic_matches:
                if (m.source_column, m.target_column) not in existing_pairs:
                    relationships.append(m)

            # 3. Value overlap for matching column types
            value_matches = _find_value_overlaps(id_a, id_b, df_a, df_b)
            relationships.extend(value_matches)

    # Deduplicate and rank by confidence
    relationships = _deduplicate_relationships(relationships)
    relationships.sort(key=lambda r: r.confidence, reverse=True)

    # Suggest key types
    relationships = _suggest_keys(relationships, datasets)

    return relationships


def _find_name_matches(
    id_a: str, id_b: str, df_a: pd.DataFrame, df_b: pd.DataFrame
) -> List[DatasetRelationship]:
    """Find columns with exact name matches (case-insensitive)."""
    matches = []
    cols_a = {c.lower(): c for c in df_a.columns}
    cols_b = {c.lower(): c for c in df_b.columns}

    common = set(cols_a.keys()) & set(cols_b.keys())
    # Skip normalized columns
    common = {c for c in common if not c.endswith("_norm")}

    for col_lower in common:
        col_a = cols_a[col_lower]
        col_b = cols_b[col_lower]

        confidence = 0.8
        # Boost confidence if types match
        if df_a[col_a].dtype == df_b[col_b].dtype:
            confidence = 0.9

        matches.append(DatasetRelationship(
            source_dataset=id_a,
            target_dataset=id_b,
            source_column=col_a,
            target_column=col_b,
            relationship_type=RelationshipType.COLUMN_NAME_MATCH,
            confidence=confidence,
        ))

    return matches


def _find_semantic_matches(
    id_a: str, id_b: str, df_a: pd.DataFrame, df_b: pd.DataFrame
) -> List[DatasetRelationship]:
    """Find semantically similar column names using string similarity."""
    matches = []
    cols_a = [c for c in df_a.columns if not c.endswith("_norm")]
    cols_b = [c for c in df_b.columns if not c.endswith("_norm")]

    for col_a in cols_a:
        for col_b in cols_b:
            if col_a.lower() == col_b.lower():
                continue  # Already handled by exact match

            similarity = SequenceMatcher(None, col_a.lower(), col_b.lower()).ratio()

            if similarity >= 0.7:
                # Check for common patterns
                common_id_patterns = ["id", "codigo", "code", "key", "clave", "numero", "num"]
                boost = 0
                for pattern in common_id_patterns:
                    if pattern in col_a.lower() and pattern in col_b.lower():
                        boost = 0.1
                        break

                matches.append(DatasetRelationship(
                    source_dataset=id_a,
                    target_dataset=id_b,
                    source_column=col_a,
                    target_column=col_b,
                    relationship_type=RelationshipType.SEMANTIC_MATCH,
                    confidence=min(similarity + boost, 1.0),
                ))

    return matches


def _find_value_overlaps(
    id_a: str, id_b: str, df_a: pd.DataFrame, df_b: pd.DataFrame
) -> List[DatasetRelationship]:
    """Find columns with significant value overlap."""
    matches = []
    cols_a = [c for c in df_a.columns if not c.endswith("_norm")]
    cols_b = [c for c in df_b.columns if not c.endswith("_norm")]

    # Precompute unique value sets to avoid O(N*M) redundant pandas operations
    sets_a = {}
    for c in cols_a:
        if 2 <= df_a[c].nunique() <= 1000:
            sets_a[c] = set(df_a[c].dropna().unique())
            
    sets_b = {}
    for c in cols_b:
        if 2 <= df_b[c].nunique() <= 1000:
            sets_b[c] = set(df_b[c].dropna().unique())

    for col_a, values_a in sets_a.items():
        for col_b, values_b in sets_b.items():
            # Must be same general type
            both_numeric = (
                pd.api.types.is_numeric_dtype(df_a[col_a])
                and pd.api.types.is_numeric_dtype(df_b[col_b])
            )
            both_string = (
                df_a[col_a].dtype == object and df_b[col_b].dtype == object
            )

            if not (both_numeric or both_string):
                continue

            try:
                if len(values_a) == 0 or len(values_b) == 0:
                    continue

                overlap = values_a & values_b
                overlap_ratio = len(overlap) / min(len(values_a), len(values_b))

                if overlap_ratio > 0.3 and len(overlap) >= 3:
                    matches.append(DatasetRelationship(
                        source_dataset=id_a,
                        target_dataset=id_b,
                        source_column=col_a,
                        target_column=col_b,
                        relationship_type=RelationshipType.VALUE_OVERLAP,
                        confidence=round(overlap_ratio, 3),
                        shared_values_count=len(overlap),
                    ))
            except Exception:
                continue

    return matches


def _deduplicate_relationships(rels: List[DatasetRelationship]) -> List[DatasetRelationship]:
    """Remove duplicate relationships, keeping highest confidence."""
    seen = {}
    for r in rels:
        key = (r.source_dataset, r.target_dataset, r.source_column, r.target_column)
        if key not in seen or r.confidence > seen[key].confidence:
            seen[key] = r
    return list(seen.values())


def _suggest_keys(
    relationships: List[DatasetRelationship],
    datasets: Dict[str, pd.DataFrame],
) -> List[DatasetRelationship]:
    """Suggest primary/foreign key types based on uniqueness."""
    for r in relationships:
        df_source = datasets.get(r.source_dataset)
        df_target = datasets.get(r.target_dataset)

        if df_source is None or df_target is None:
            continue

        try:
            source_unique = df_source[r.source_column].nunique() == len(df_source)
            target_unique = df_target[r.target_column].nunique() == len(df_target)

            if source_unique and not target_unique:
                r.suggested_key_type = "primary→foreign"
            elif target_unique and not source_unique:
                r.suggested_key_type = "foreign→primary"
            elif source_unique and target_unique:
                r.suggested_key_type = "one-to-one"
            else:
                r.suggested_key_type = "many-to-many"
        except Exception:
            r.suggested_key_type = "unknown"

    return relationships
