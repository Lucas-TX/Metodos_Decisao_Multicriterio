import numpy as np

def calcular_ahp(matrix):
    # Soma conteúdo das colunas
    column_sums = matrix.sum(axis=0)

    # Operação element-wise para normalizar a matriz (dividir cada elemento pela soma da coluna correspondente)
    normalized_matrix = matrix / column_sums

    # Soma conteúdo das linhas da matriz normalizada e divide pela quantidade de colunas para obter o vetor de prioridade (autovetor principal)
    priority_vector = normalized_matrix.mean(axis=1)

    # Multiplicação da matriz original (A) pelo vetor de prioridade (w) para obter o vetor ponderado
    weighted_sum = matrix.dot(priority_vector)

    # Divisão por elemento entre o vetor ponderado e o vetor de prioridade para obter o vetor de consistência, cujo valor médio é o autovalor principal (λmax)
    consistency_vector = weighted_sum / priority_vector
    lambda_max = consistency_vector.mean()

    n = len(matrix)

    # CI (Consistency Index)
    CI = (lambda_max - n) / (n - 1)

    # RI (Random Index - tabela Saaty)
    ri_table = {
        1: 0.00,
        2: 0.00,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49
    }

    RI = ri_table.get(n, None)

    # CR (Consistency Ratio)
    CR = CI / RI if RI and RI != 0 else None

    return {
        "column_sums": column_sums,
        "normalized_matrix": normalized_matrix,
        "priority_vector": priority_vector,
        "weighted_sum": weighted_sum,
        "consistency_vector": consistency_vector,
        "lambda_max": lambda_max,
        "CI": CI,
        "CR": CR
    }