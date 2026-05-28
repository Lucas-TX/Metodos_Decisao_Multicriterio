import numpy as np


def calcular_dematel(matrix):
    """
    Executa o método DEMATEL.

    Parâmetros:
    matrix:
        Matriz de influência direta.
        Linhas = fatores que influenciam.
        Colunas = fatores influenciados.

    Regras esperadas:
    - Matriz quadrada
    - Diagonal principal igual a zero
    - Valores de influência normalmente entre 0 e 4

    Retorno:
        Dicionário com matrizes intermediárias e resultados finais.
    """

    # Converte entrada para array NumPy
    matrix = np.array(matrix, dtype=float)


    # Função Shape pega o número de linhas da matriz.
    n = matrix.shape[0]

    # Soma das linhas e colunas da matriz Z
    row_sums_z = np.sum(matrix, axis=1) # Soma linhas 
    col_sums_z = np.sum(matrix, axis=0) # Soma colunas

    # Captura o maior valor entre as somas das linhas e colunas para calcular Lambda
    max_row_sum = np.max(row_sums_z)
    max_col_sum = np.max(col_sums_z)

    # Validação para garantir que a matriz não esteja zerada.
    if max_row_sum == 0 and max_col_sum == 0:
        raise ValueError(
            "A matriz está toda zerada. Informe pelo menos uma influência diferente de zero."
        )

    # Constante de normalização lambda
    lambda_row = (1 / max_row_sum) if max_row_sum > 0 else np.inf
    lambda_col = (1 / max_col_sum) if max_col_sum > 0 else np.inf
    lambda_value = min(lambda_row, lambda_col)

    # Matriz normalizada D
    normalized_matrix = lambda_value * matrix

    # Matriz identidade
    identity_matrix = np.eye(n)

    # Matriz (I - D)
    identity_minus_normalized = identity_matrix - normalized_matrix

    # Inversa de (I - D)
    try:
        inverse_identity_minus_normalized = np.linalg.inv(identity_minus_normalized)
    except np.linalg.LinAlgError:
        raise ValueError(
            "Não foi possível calcular a inversa de (I - D). Verifique os valores da matriz."
        )

    # Matriz de relação total T
    total_relation_matrix = normalized_matrix @ inverse_identity_minus_normalized # @ é operador de multiplicação de matrizes em NumPy

    # Vetor r = soma das linhas de T
    r = np.sum(total_relation_matrix, axis=1)

    # Vetor c = soma das colunas de T
    c = np.sum(total_relation_matrix, axis=0)

    # Proeminência e relação
    prominence = r + c
    relation = r - c

    # Classificação dos fatores
    classification = np.where(
        relation > 0,
        "Causa",
        np.where(relation < 0, "Efeito", "Neutro")
    )

    # Limiar alpha = média dos elementos de T
    alpha = np.mean(total_relation_matrix)

    # Matriz T filtrada pelo limiar
    threshold_matrix = np.where(total_relation_matrix >= alpha, total_relation_matrix, 0.0)

    # Coordenadas para o mapa de influência
    # x = r + c
    # y = r - c
    coordinates = np.column_stack((prominence, relation))

    # Lista de nós para o gráfico
    # Cada nó representa um fator
    nodes = []
    for i in range(n):
        nodes.append({
            "id": i,
            "label": f"F{i+1}",
            "x": float(coordinates[i, 0]),   # r + c
            "y": float(coordinates[i, 1]),   # r - c
            "r": float(r[i]),
            "c": float(c[i]),
            "prominence": float(prominence[i]),
            "relation": float(relation[i]),
            "classification": classification[i]
        })

    # Lista de arestas para o gráfico
    # Cada aresta representa uma relação relevante da matriz T filtrada
    edges = []
    for i in range(n):
        for j in range(n):
            if i != j and threshold_matrix[i, j] > 0:
                edges.append({
                    "source": i,
                    "target": j,
                    "weight": float(threshold_matrix[i, j])
                })

    return{
            "z_matrix": matrix,
            "lambda_value": lambda_value,
            "normalized_matrix": normalized_matrix,
            "identity_minus_normalized": identity_minus_normalized,
            "inverse_identity_minus_normalized": inverse_identity_minus_normalized,
            "total_relation_matrix": total_relation_matrix,
            "r": r,
            "c": c,
            "prominence": prominence,
            "relation": relation,
            "classification": classification,
            "alpha": alpha,
            "threshold_matrix": threshold_matrix,
            "coordinates": coordinates,
            "edges": edges,
            "nodes": nodes
        }