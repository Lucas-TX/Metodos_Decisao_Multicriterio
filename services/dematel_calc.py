import numpy as np


def normalize_direct_relation(matrix):
    """Normalize a direct-relation matrix for DEMATEL."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Direct relation matrix must be square.")

    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)
    max_sum = max(np.max(row_sums), np.max(col_sums))
    if max_sum == 0:
        raise ValueError("Cannot normalize a zero matrix.")

    return matrix / max_sum


def total_relation_matrix(normalized_matrix):
    """Compute the total relation matrix T = N(I - N)^-1."""
    normalized_matrix = np.asarray(normalized_matrix, dtype=float)
    n = normalized_matrix.shape[0]
    if normalized_matrix.ndim != 2 or normalized_matrix.shape[0] != normalized_matrix.shape[1]:
        raise ValueError("Normalized matrix must be square.")

    identity = np.eye(n)
    try:
        inverse = np.linalg.inv(identity - normalized_matrix)
    except np.linalg.LinAlgError as ex:
        raise ValueError("Matrix (I - N) is singular and cannot be inverted.") from ex

    return normalized_matrix @ inverse


def cause_effect_vectors(total_matrix):
    """Compute D, R, D+R and D-R vectors from the total relation matrix."""
    total_matrix = np.asarray(total_matrix, dtype=float)
    if total_matrix.ndim != 2 or total_matrix.shape[0] != total_matrix.shape[1]:
        raise ValueError("Total relation matrix must be square.")

    d = total_matrix.sum(axis=1)
    r = total_matrix.sum(axis=0)
    return d, r, d + r, d - r


def classify_cause_effect(d_minus_r):
    """Classify factors into cause and effect groups."""
    d_minus_r = np.asarray(d_minus_r, dtype=float)
    return np.where(d_minus_r >= 0, "cause", "effect")


def threshold_matrix(total_matrix, threshold=None):
    """Apply a threshold to the total relation matrix."""
    total_matrix = np.asarray(total_matrix, dtype=float)
    if threshold is None:
        return total_matrix.copy()

    if threshold < 0:
        raise ValueError("Threshold must be non-negative.")

    thresholded = np.where(np.abs(total_matrix) >= threshold, total_matrix, 0.0)
    return thresholded


def dematel(direct_matrix, threshold=None):
    """Compute DEMATEL results from a direct relation matrix.

    Returns a dictionary with:
        normalized: normalized direct-relation matrix
        total: total relation matrix
        d: row sums (influence given)
        r: column sums (influence received)
        centrality: d + r vector
        relation: d - r vector
        classification: cause/effect labels
        thresholded: thresholded total relation matrix
    """
    normalized = normalize_direct_relation(direct_matrix)
    total = total_relation_matrix(normalized)
    d, r, centrality, relation = cause_effect_vectors(total)
    classification = classify_cause_effect(relation)
    thresholded = threshold_matrix(total, threshold)

    return {
        "normalized": normalized,
        "total": total,
        "d": d,
        "r": r,
        "centrality": centrality,
        "relation": relation,
        "classification": classification,
        "thresholded": thresholded,
    }


def display_dematel_results(results, factor_labels=None):
    """Return a summary of DEMATEL results for reporting."""
    labels = None
    if factor_labels is not None:
        if len(factor_labels) != results["normalized"].shape[0]:
            raise ValueError("factor_labels length must match matrix dimension.")
        labels = list(factor_labels)
    else:
        labels = [f"F{i+1}" for i in range(results["normalized"].shape[0])]

    summary = {
        "normalized": results["normalized"],
        "total": results["total"],
        "d": dict(zip(labels, results["d"])),
        "r": dict(zip(labels, results["r"])),
        "centrality": dict(zip(labels, results["centrality"])),
        "relation": dict(zip(labels, results["relation"])),
        "classification": dict(zip(labels, results["classification"])),
    }
    return summary
