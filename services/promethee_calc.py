from __future__ import annotations
import math
from typing import Dict, List, Any
import numpy as np
import pandas as pd

#TODO #2 Validar cálculo Promethee com exemplo conhecido (ex: Brans 1986) para garantir que as fórmulas estão corretas e os resultados fazem sentido.

# =========================================================
# Funções de preferência
# =========================================================
def preference_degree(
    d: float,
    func_name: str,
    q: float = 0.0,
    p: float = 1.0,
    s: float = 1.0,
) -> float:
    """
    Calcula o grau de preferência P(d) no intervalo [0, 1].

    Premissa:
    - d > 0 significa que a alternativa 'a' é melhor que 'b' no critério.
    - d <= 0 implica ausência de preferência (P = 0).
    """
    if pd.isna(d):
        return 0.0

    d = float(d)

    if func_name == "Tipo 1: Usual":
        return 1.0 if d > 0 else 0.0

    if func_name == "Tipo 2: U-Shape":
        return 0.0 if d <= q else 1.0

    if func_name == "Tipo 3: V-Shape":
        if d <= 0:
            return 0.0
        pp = max(float(p), 1e-12)
        return min(d / pp, 1.0)

    if func_name == "Tipo 4: Nível":
        if d <= q:
            return 0.0
        pp = max(float(p), float(q) + 1e-12)
        if d <= pp:
            return 0.5
        return 1.0

    if func_name == "Tipo 5: Linear":
        if d <= q:
            return 0.0
        pp = max(float(p), float(q) + 1e-12)
        if d < pp:
            return (d - q) / (pp - q)
        return 1.0

    if func_name == "Tipo 6: Gaussiano":
        if d <= 0:
            return 0.0
        ss = max(float(s), 1e-12)
        return 1.0 - math.exp(-(d ** 2) / (2.0 * ss ** 2))

    raise ValueError(f"Função de preferência não reconhecida: {func_name}")


# =========================================================
# Validação / preparação
# =========================================================
def _validate_inputs(criteria: List[Dict[str, Any]], decision_df_numeric: pd.DataFrame) -> None:
    
    criterion_names = [c["name"] for c in criteria]
    missing_cols = [name for name in criterion_names if name not in decision_df_numeric.columns]
    if missing_cols:
        raise ValueError(
            f"As seguintes colunas estão ausentes na matriz de decisão: {missing_cols}"
        )

def _normalized_weights(criteria: List[Dict[str, Any]]) -> np.ndarray:
    weights = np.array([float(c.get("peso", 0.0)) for c in criteria], dtype=float)

    if np.any(weights < 0):
        raise ValueError("Os pesos dos critérios não podem ser negativos.")

    total = weights.sum()
    if total <= 0:
        weights = np.ones(len(criteria), dtype=float) / len(criteria)
    else:
        weights = weights / total

    return weights


def _pairwise_difference(a_val: float, b_val: float, objetivo: str) -> float:
    """
    Retorna a diferença já ajustada para o objetivo do critério.

    Maximização: d = a - b
    Minimização: d = b - a
    """
    if pd.isna(a_val) or pd.isna(b_val):
        return np.nan

    if objetivo == "Maximização":
        return float(a_val) - float(b_val)
    elif objetivo == "Minimização":
        return float(b_val) - float(a_val)
    else:
        raise ValueError(f"Objetivo inválido: {objetivo}")


# =========================================================
# Cálculo principal
# =========================================================
def compute_promethee(
    criteria: List[Dict[str, Any]],
    decision_df_numeric: pd.DataFrame,
    epsilon: float = 1e-9,
) -> Dict[str, Any]:
    """
    Executa o cálculo do PROMETHEE I e II.

    Parâmetros esperados
    --------------------
    criteria : list[dict]
        Lista de critérios no mesmo formato usado pelo Promethee.py.
        Cada item deve conter pelo menos:
        - name
        - objetivo  -> "Maximização" ou "Minimização"
        - peso
        - funcao_pref
        - q, p, s (quando aplicável)

    decision_df_numeric : pd.DataFrame
        Matriz numérica com:
        - índice = alternativas
        - colunas = nomes dos critérios

    Retorno
    -------
    dict com:
        - normalized_weights
        - unicriterion_preference_matrices
        - aggregate_preference_matrix
        - unicriterion_flows
        - flows
        - ranking
        - promethee_i_relations
        - criterion_contributions
    """
    _validate_inputs(criteria, decision_df_numeric)

    alternatives = list(decision_df_numeric.index)
    criterion_names = [c["name"] for c in criteria]

    X = decision_df_numeric[criterion_names].copy().astype(float)
    n = len(alternatives)
    m = len(criteria)

    weights = _normalized_weights(criteria)

    # Matrizes unicritério P_k(a,b)
    unicriterion_pref = {}
    aggregate_pref = np.zeros((n, n), dtype=float)

    for k, c in enumerate(criteria):
        cname = c["name"]
        objetivo = c["objetivo"]
        func_name = c["funcao_pref"]
        q = float(c.get("q", 0.0))
        p = float(c.get("p", 1.0))
        s = float(c.get("s", 1.0))

        values = X[cname].to_numpy(dtype=float)
        pref_matrix = np.zeros((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                if i == j:
                    pref_matrix[i, j] = 0.0
                    continue

                d = _pairwise_difference(values[i], values[j], objetivo)
                pref_matrix[i, j] = preference_degree(
                    d=d,
                    func_name=func_name,
                    q=q,
                    p=p,
                    s=s,
                )

        unicriterion_pref[cname] = pd.DataFrame(
            pref_matrix,
            index=alternatives,
            columns=alternatives,
        )

        aggregate_pref += weights[k] * pref_matrix

    aggregate_pref_df = pd.DataFrame(
        aggregate_pref,
        index=alternatives,
        columns=alternatives,
    )

    # Fluxos multicritério
    divisor = max(n - 1, 1)
    phi_plus = aggregate_pref.sum(axis=1) / divisor
    phi_minus = aggregate_pref.sum(axis=0) / divisor
    phi_net = phi_plus - phi_minus

    flows_df = pd.DataFrame({
        "Alternativa": alternatives,
        "Phi+": phi_plus,
        "Phi-": phi_minus,
        "Phi": phi_net,
    }).set_index("Alternativa")

    ranking_df = (
        flows_df.sort_values("Phi", ascending=False)
        .reset_index()
        .rename(columns={"index": "Alternativa"})
    )
    ranking_df.insert(0, "Rank", np.arange(1, len(ranking_df) + 1))

    # Fluxos unicritério
    unicriterion_flow_rows = []
    criterion_contributions = pd.DataFrame(index=alternatives)

    for k, c in enumerate(criteria):
        cname = c["name"]
        pk = unicriterion_pref[cname].to_numpy(dtype=float)

        phi_plus_k = pk.sum(axis=1) / divisor
        phi_minus_k = pk.sum(axis=0) / divisor
        phi_k = phi_plus_k - phi_minus_k

        for i, alt in enumerate(alternatives):
            unicriterion_flow_rows.append({
                "Critério": cname,
                "Alternativa": alt,
                "Phi+_k": phi_plus_k[i],
                "Phi-_k": phi_minus_k[i],
                "Phi_k": phi_k[i],
                "Peso normalizado": weights[k],
                "Contribuição ponderada": weights[k] * phi_k[i],
            })

        criterion_contributions[cname] = weights[k] * phi_k

    unicriterion_flows_df = pd.DataFrame(unicriterion_flow_rows)

    # PROMETHEE I - Relações parciais
    # P: preferível, I: indiferente, R: incomparável, -: diagonal
    relation_matrix = pd.DataFrame(
        "",
        index=alternatives,
        columns=alternatives,
    )

    for a in alternatives:
        for b in alternatives:
            if a == b:
                relation_matrix.loc[a, b] = "-"
                continue

            phi_plus_a = flows_df.loc[a, "Phi+"]
            phi_plus_b = flows_df.loc[b, "Phi+"]
            phi_minus_a = flows_df.loc[a, "Phi-"]
            phi_minus_b = flows_df.loc[b, "Phi-"]

            # a P b se:
            # Phi+(a) >= Phi+(b) e Phi-(a) <= Phi-(b), com pelo menos uma estrita
            cond_pref = (
                (phi_plus_a >= phi_plus_b - epsilon) and
                (phi_minus_a <= phi_minus_b + epsilon) and
                (
                    (phi_plus_a > phi_plus_b + epsilon) or
                    (phi_minus_a < phi_minus_b - epsilon)
                )
            )

            # a I b se ambos praticamente iguais
            cond_indiff = (
                abs(phi_plus_a - phi_plus_b) <= epsilon and
                abs(phi_minus_a - phi_minus_b) <= epsilon
            )

            if cond_indiff:
                relation_matrix.loc[a, b] = "I"
            elif cond_pref:
                relation_matrix.loc[a, b] = "P"
            else:
                relation_matrix.loc[a, b] = "R"

    result = {
        "normalized_weights": pd.DataFrame({
            "Critério": criterion_names,
            "Peso normalizado": weights,
        }),
        "unicriterion_preference_matrices": unicriterion_pref,
        "aggregate_preference_matrix": aggregate_pref_df,
        "unicriterion_flows": unicriterion_flows_df,
        "flows": flows_df,
        "ranking": ranking_df,
        "promethee_i_relations": relation_matrix,
        "criterion_contributions": criterion_contributions,
    }

    return result


# =========================================================
# Função utilitária para uso direto no Promethee.py
# =========================================================
def run_promethee_from_streamlit_state(
    criteria: List[Dict[str, Any]],
    decision_df_numeric: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Função fina para chamada direta a partir do arquivo Promethee.py.
    """
    return compute_promethee(criteria=criteria, decision_df_numeric=decision_df_numeric)