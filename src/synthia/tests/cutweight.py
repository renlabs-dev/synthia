def cut_to_max_allowed_weights(
    score_dict: dict[int, float], settings: None = None
) -> dict[int, float]:
    """
    Cuts the scores to the maximum allowed weights.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.

    Returns:
            dict[int, float]: A dictionary mapping miner UIDs to their scores,
            where the scores have been cut to the maximum allowed weights.
    """

    # max_allowed_weights = settings.max_allowed_weights
    max_allowed_weights = 5

    # sort the score by highest to lowest
    sorted_scores = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)

    # cut to max_allowed_weights
    cut_scores = sorted_scores[:max_allowed_weights]

    return dict(cut_scores)


if __name__ == "__main__":
    test_weights : dict[int, float] = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
    print(cut_to_max_allowed_weights(test_weights))