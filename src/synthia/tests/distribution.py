import math

def sigmoid(x: float):
    return 1 / (1 + math.exp(-x))

def adjust_distribution(score_dict: dict[int, float]) -> dict[int, float]:
    """
    Adjusts the distribution of scores, such that the best miners are rewarded significantly more than the rest.
    This ensures that it's profitable to run a high-end model, in comparison to cheap models.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.

    Returns:
        A dictionary mapping miner UIDs to their adjusted scores.
    """
    # Calculate the mean score
    mean_score = sum(score_dict.values()) / len(score_dict)

    # Set the threshold as a percentage above the mean score
    threshold_percentage = 0.2  
    threshold = mean_score * (1 + threshold_percentage)

   
    steepness = 20.0  # steepness for sharper punishment

    # Set the high and low rewards
    high_reward = 1.0
    low_reward = 0.01  

    # Calculate the adjusted scores using the sigmoid function
    adjusted_scores : dict[int, float] = {}
    for model_id, score in score_dict.items():
        normalized_score = (score - threshold) * steepness
        reward_ratio = sigmoid(normalized_score)
        adjusted_score = low_reward + (high_reward - low_reward) * reward_ratio
        adjusted_scores[model_id] = adjusted_score

    return adjusted_scores

def convert_weights(score_dict: dict[int, float],):
  # Create a new dictionary to store the weighted scores
    weighted_scores: dict[int, int] = {}

    # Calculate the sum of all inverted scores
    scores = sum(score_dict.values())

    # Iterate over the items in the score_dict
    for uid, score in score_dict.items():
        # Calculate the normalized weight as an integer
        weight = int(score / scores * 100)

        # Add the weighted score to the new dictionary
        weighted_scores[uid] = weight

    # filter out 0 weights
    weighted_scores = {k: v for k, v in weighted_scores.items() if v != 0}

    uids = list(weighted_scores.keys())
    weights = list(weighted_scores.values())

    return uids, weights

if __name__ == "__main__":
    score_dict = {0: 0.649414, 
                 1: 0.688499, 	
                 2: 0.85842, # opus
                 3: 0.706486, 
                 4: 0.805593, 
                 5: 0.835922, # opus
                 6: 0.737698,
                 7: 0.686483, 
                 8: 0.746951, # opus
                 9: 0.602256, 
                 10: 0.734287, 
                 11: 0.663901, 
                 12: 0.72661,
                 13: 0.785198, # opus
                 14: 0,
    }

    adjusted_distribution = (adjust_distribution(score_dict))
    weights, uids = convert_weights(adjusted_distribution)
    zipped_weights = list(zip(weights, uids))
    print(zipped_weights)
