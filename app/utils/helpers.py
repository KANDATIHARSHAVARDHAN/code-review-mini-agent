from typing import List


def score_to_grade(score: float) -> str:
    if score >= 0.9:
        return "A"
    if score >= 0.75:
        return "B"
    if score >= 0.5:
        return "C"
    return "D"
