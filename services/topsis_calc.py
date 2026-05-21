import numpy as np


def calcular_topsis(matrix, weights, criteria_types):
    """
    Executa o método TOPSIS.

    Parâmetros:
    matrix:
        Matriz de decisão.
        Linhas = critérios.
        Colunas = alternativas.

    weights:
        Lista ou array com os pesos dos critérios.
        Deve ter o mesmo tamanho da quantidade de linhas da matriz.

    criteria_types:
        Lista indicando o tipo de cada critério.
        Valores esperados:
            "Maximização"
            "Minimização"

    Retorno:
        Dicionário com as matrizes intermediárias, distâncias, scores e ranking.
    """

    # Converte entradas para arrays NumPy
    matrix = np.array(matrix, dtype=float)
    weights = np.array(weights, dtype=float)

    # Normaliza os pesos
    normalized_weights = weights / weights.sum()

    # Soma dos quadrados por critério
    # Como as linhas são critérios, a normalização é feita por linha
    row_square_sums = np.sum(matrix ** 2, axis=1)

    # Raiz da soma dos quadrados por critério
    row_norms = np.sqrt(row_square_sums)

    # Matriz normalizada
    normalized_matrix = matrix / row_norms[:, np.newaxis]

    # Matriz normalizada ponderada
    weighted_normalized_matrix = normalized_matrix * normalized_weights[:, np.newaxis]

    # Definição da solução ideal positiva e negativa
    ideal_positive = []
    ideal_negative = []

    for i, criteria_type in enumerate(criteria_types):

        if criteria_type == "Maximização":
            ideal_positive.append(weighted_normalized_matrix[i, :].max())
            ideal_negative.append(weighted_normalized_matrix[i, :].min())

        elif criteria_type == "Minimização":
            ideal_positive.append(weighted_normalized_matrix[i, :].min())
            ideal_negative.append(weighted_normalized_matrix[i, :].max())

        else:
            raise ValueError(
                "Tipo de critério inválido. Use 'Maximização' ou 'Minimização'."
            )

    ideal_positive = np.array(ideal_positive)
    ideal_negative = np.array(ideal_negative)

    # Distância de cada alternativa em relação à solução ideal positiva
    distance_positive = np.sqrt(
        np.sum(
            (weighted_normalized_matrix - ideal_positive[:, np.newaxis]) ** 2,
            axis=0
        )
    )

    # Distância de cada alternativa em relação à solução ideal negativa
    distance_negative = np.sqrt(
        np.sum(
            (weighted_normalized_matrix - ideal_negative[:, np.newaxis]) ** 2,
            axis=0
        )
    )

    # Score TOPSIS
    scores = distance_negative / (distance_positive + distance_negative)

    # Ranking
    # Maior score = melhor alternativa
    ranking = np.argsort(-scores) + 1

    # Posição no ranking para cada alternativa
    ranking_positions = np.empty_like(ranking)
    ranking_positions[ranking - 1] = np.arange(1, len(scores) + 1)

    return {
        "weights": weights,
        "normalized_weights": normalized_weights,
        "row_square_sums": row_square_sums,
        "row_norms": row_norms,
        "normalized_matrix": normalized_matrix,
        "weighted_normalized_matrix": weighted_normalized_matrix,
        "ideal_positive": ideal_positive,
        "ideal_negative": ideal_negative,
        "distance_positive": distance_positive,
        "distance_negative": distance_negative,
        "scores": scores,
        "ranking_positions": ranking_positions,
        "ranking_order": ranking
    }