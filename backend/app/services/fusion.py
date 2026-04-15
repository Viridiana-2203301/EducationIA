"""
Dataset Fusion Service.
Automatically joins datasets using detected relationships.
Supports inner join, left join, and multi-table joins.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from app.schemas.schemas import DatasetRelationship


def reduce_fused_dimensions(
    fused_dfs: Dict[str, pd.DataFrame],
    n_components: int = 10,
    variance_threshold: float = 0.95,
) -> Dict[str, pd.DataFrame]:
    """
    Aplica PCA a cada dataset fusionado para reducir dimensiones.
    Conserva columnas categóricas (como tipo_educacion) y reemplaza
    las columnas numéricas por los componentes principales.
    """
    reduced: Dict[str, pd.DataFrame] = {}

    for key, df in fused_dfs.items():
        try:
            # Separar columnas numéricas y categóricas
            numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                           if not c.endswith("_norm")]
            cat_cols = [c for c in df.columns if c not in numeric_cols]

            if len(numeric_cols) < 3:
                # No tiene sentido reducir con menos de 3 columnas numéricas
                continue

            numeric_df = df[numeric_cols].copy()

            # Eliminar filas con NaN en las columnas numéricas
            valid_mask = numeric_df.notna().all(axis=1)
            numeric_clean = numeric_df[valid_mask]
            cat_clean = df.loc[valid_mask, cat_cols] if cat_cols else pd.DataFrame(index=numeric_clean.index)

            if len(numeric_clean) < 5:
                continue

            # Reemplazar infinitos
            numeric_clean = numeric_clean.replace([np.inf, -np.inf], np.nan).dropna()
            cat_clean = cat_clean.loc[numeric_clean.index]

            # Escalar
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(numeric_clean)

            # Determinar n_components óptimo
            max_components = min(len(numeric_cols), len(numeric_clean) - 1, 50)
            pca_full = PCA(n_components=max_components)
            pca_full.fit(X_scaled)

            # Encontrar cuántos componentes explican variance_threshold
            cumulative = np.cumsum(pca_full.explained_variance_ratio_)
            optimal_n = int(np.searchsorted(cumulative, variance_threshold) + 1)
            optimal_n = max(2, min(optimal_n, n_components, max_components))

            # Aplicar PCA con el número óptimo
            pca = PCA(n_components=optimal_n)
            X_reduced = pca.fit_transform(X_scaled)

            # Crear DataFrame reducido
            pca_columns = [f"PC{i+1}" for i in range(optimal_n)]
            reduced_df = pd.DataFrame(X_reduced, columns=pca_columns, index=numeric_clean.index)

            # Agregar columnas categóricas de vuelta
            for col in cat_cols:
                reduced_df[col] = cat_clean[col].values

            # Agregar info de varianza explicada como metadata
            variance_info = {f"PC{i+1}_var": round(v, 4) for i, v in enumerate(pca.explained_variance_ratio_)}
            total_var = round(sum(pca.explained_variance_ratio_), 4)

            reduced_key = f"pca_{key}_({optimal_n}comp_{total_var}var)"
            reduced[reduced_key] = reduced_df.reset_index(drop=True)

            print(f"PCA {key}: {len(numeric_cols)} cols → {optimal_n} componentes "
                  f"({total_var*100:.1f}% varianza explicada)")

        except Exception as e:
            print(f"Error aplicando PCA a {key}: {e}")
            import traceback
            traceback.print_exc()

    return reduced


def auto_concat_datasets(
    datasets: Dict[str, pd.DataFrame],
    dataset_names: Dict[str, str],
) -> Dict[str, pd.DataFrame]:
    """
    Concatenar TODOS los datasets en uno solo.
    Usa join='outer' para conservar todas las columnas.
    Las columnas que no existan en algún archivo se llenan con NaN.
    """
    concatenated: Dict[str, pd.DataFrame] = {}
    if len(datasets) < 2:
        return concatenated

    dfs_to_concat = []
    for ds_id, df in datasets.items():
        df_copy = df.copy()
        # Asegurar que tipo_educacion exista
        if 'tipo_educacion' not in df_copy.columns:
            name = dataset_names.get(ds_id, ds_id)
            df_copy['tipo_educacion'] = name
        dfs_to_concat.append(df_copy)

    try:
        # Concatenar TODOS con outer join
        concat_df = pd.concat(dfs_to_concat, ignore_index=True, join='outer')
        key = f"dataset_completo_{len(datasets)}_archivos"
        concatenated[key] = concat_df
        print(f"Dataset unificado: {len(concat_df)} filas × {len(concat_df.columns)} columnas "
              f"(de {len(datasets)} archivos)")
    except Exception as e:
        print(f"Error concatenando datasets: {e}")

    return concatenated



def auto_fuse_datasets(
    datasets: Dict[str, pd.DataFrame],
    relationships: List[DatasetRelationship],
    dataset_names: Dict[str, str],
) -> Dict[str, pd.DataFrame]:
    """
    Automatically fuse datasets based on detected relationships.
    Returns dict of fused dataset name -> DataFrame.
    """
    fused: Dict[str, pd.DataFrame] = {}

    if len(relationships) == 0 or len(datasets) < 2:
        return fused

    # Sort relationships by confidence
    sorted_rels = sorted(relationships, key=lambda r: r.confidence, reverse=True)

    # Track which datasets have been fused
    fused_pairs = set()
    
    MAX_PAIRWISE_FUSIONS = 5
    fusions_created = 0

    for rel in sorted_rels:
        if fusions_created >= MAX_PAIRWISE_FUSIONS:
            break
        pair_key = tuple(sorted([rel.source_dataset, rel.target_dataset]))

        if pair_key in fused_pairs:
            continue

        df_source = datasets.get(rel.source_dataset)
        df_target = datasets.get(rel.target_dataset)

        if df_source is None or df_target is None:
            continue

        source_name = dataset_names.get(rel.source_dataset, rel.source_dataset)
        target_name = dataset_names.get(rel.target_dataset, rel.target_dataset)

        # Get all relationships between this pair
        pair_rels = [
            r for r in sorted_rels
            if tuple(sorted([r.source_dataset, r.target_dataset])) == pair_key
        ]

        # Use the best relationship for the join
        best_rel = pair_rels[0]

        try:
            # Inner Join
            inner_key = f"inner_{source_name}_x_{target_name}"
            inner_df = _safe_merge(
                df_source, df_target,
                best_rel.source_column, best_rel.target_column,
                how="inner",
                suffixes=(f"_{source_name}", f"_{target_name}")
            )
            if inner_df is not None and len(inner_df) > 0:
                fused[inner_key] = inner_df
                fusions_created += 1

            # Left Join
            left_key = f"left_{source_name}_x_{target_name}"
            left_df = _safe_merge(
                df_source, df_target,
                best_rel.source_column, best_rel.target_column,
                how="left",
                suffixes=(f"_{source_name}", f"_{target_name}")
            )
            if left_df is not None and len(left_df) > 0:
                fused[left_key] = left_df
                fusions_created += 1

            fused_pairs.add(pair_key)

        except Exception as e:
            print(f"Error fusing {source_name} x {target_name}: {e}")
            continue

    # Multi-table join: try to chain the top relationships
    if len(sorted_rels) >= 2 and len(datasets) >= 3:
        multi_df = _multi_table_join(datasets, sorted_rels, dataset_names)
        if multi_df is not None and len(multi_df) > 0:
            fused["multi_table_join"] = multi_df

    return fused


def _safe_merge(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    left_col: str,
    right_col: str,
    how: str = "inner",
    suffixes: Tuple[str, str] = ("_left", "_right"),
) -> Optional[pd.DataFrame]:
    """Safe merge with type coercion and error handling."""
    try:
        left = df_left.copy()
        right = df_right.copy()

        # Ensure join columns are same type
        left[left_col] = left[left_col].astype(str).fillna("nan")
        right[right_col] = right[right_col].astype(str).fillna("nan")

        # Build a bulletproof estimate of output size avoiding any pandas NA drop quirks
        vc_left = left[left_col].value_counts(dropna=False)
        vc_right = right[right_col].value_counts(dropna=False)
        
        est_rows = 0
        for val, count in vc_left.items():
            if val in vc_right.index:
                est_rows += count * vc_right[val]
                
        if how == "left":
            est_rows += len(left)
            
        if est_rows > 500000:
            print(f"Merge aborted: Cartesian explosion ({est_rows} rows projected).")
            return None
        elif est_rows == 0 and how == "inner":
            return pd.DataFrame()

        # Remove _norm columns to reduce clutter
        left = left[[c for c in left.columns if not c.endswith("_norm")]]
        right = right[[c for c in right.columns if not c.endswith("_norm")]]

        if left_col == right_col:
            result = pd.merge(left, right, on=left_col, how=how, suffixes=suffixes)
        else:
            result = pd.merge(
                left, right,
                left_on=left_col, right_on=right_col,
                how=how, suffixes=suffixes
            )

        # Limit result size for memory safety
        if len(result) > 100000:
            result = result.head(100000)

        return result

    except Exception as e:
        print(f"Merge error: {e}")
        return None


def _multi_table_join(
    datasets: Dict[str, pd.DataFrame],
    relationships: List[DatasetRelationship],
    dataset_names: Dict[str, str],
) -> Optional[pd.DataFrame]:
    """
    Chain joins across multiple datasets.
    Uses BFS to find the longest chain of joinable datasets.
    """
    try:
        # Build adjacency list
        adj: Dict[str, List[Tuple[str, DatasetRelationship]]] = {}
        for rel in relationships:
            if rel.source_dataset not in adj:
                adj[rel.source_dataset] = []
            if rel.target_dataset not in adj:
                adj[rel.target_dataset] = []
            adj[rel.source_dataset].append((rel.target_dataset, rel))
            adj[rel.target_dataset].append((rel.source_dataset, DatasetRelationship(
                source_dataset=rel.target_dataset,
                target_dataset=rel.source_dataset,
                source_column=rel.target_column,
                target_column=rel.source_column,
                relationship_type=rel.relationship_type,
                confidence=rel.confidence,
            )))

        # Start from dataset with most connections
        start = max(adj.keys(), key=lambda k: len(adj[k]))

        # BFS chain
        visited = {start}
        result_df = datasets[start].copy()
        result_df = result_df[[c for c in result_df.columns if not c.endswith("_norm")]]

        queue = list(adj.get(start, []))
        join_count = 0

        for neighbor, rel in queue:
            if neighbor in visited or join_count >= 3:
                break
            visited.add(neighbor)

            neighbor_df = datasets[neighbor].copy()
            neighbor_df = neighbor_df[[c for c in neighbor_df.columns if not c.endswith("_norm")]]

            name = dataset_names.get(neighbor, neighbor)

            merged = _safe_merge(
                result_df, neighbor_df,
                rel.source_column, rel.target_column,
                how="inner",
                suffixes=("", f"_{name}")
            )

            if merged is not None and len(merged) > 0:
                result_df = merged
                join_count += 1

        return result_df if join_count > 0 else None

    except Exception as e:
        print(f"Multi-table join error: {e}")
        return None
