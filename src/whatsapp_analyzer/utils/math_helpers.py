"""
Mathematical helper functions for WhatsApp chat analysis.
"""

import math


def gcd(a: int, b: int) -> int:
    """
    Calculate greatest common divisor using Euclidean algorithm.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Greatest common divisor
    """
    if b == 0:
        return a
    return gcd(b, a % b)


def findnum(str_val: str) -> int:
    """
    Find the smallest integer k such that k * str becomes natural.

    Used for converting decimal percentages to fractions.

    Args:
        str_val: String representation of a floating point number

    Returns:
        Denominator for fraction representation
    """
    n = len(str_val)
    count_after_dot = 0
    dot_seen = 0
    num = 0

    for i in range(n):
        if str_val[i] != '.':
            num = num * 10 + int(str_val[i])
            if dot_seen == 1:
                count_after_dot += 1
        else:
            dot_seen = 1

    # If there was no dot, number is already a natural
    if dot_seen == 0:
        return 1

    # Find denominator in fraction form
    dem = int(math.pow(10, count_after_dot))

    # Result is denominator divided by GCD
    return int(dem / gcd(num, dem))


def percent_helper(percent: float) -> str:
    """
    Convert a percentage to a human-readable fraction description.

    Examples:
        0.25 -> "1 out of 4 messages"
        0.33 -> "1 out of 3 messages"
        0.005 -> "<1 out of 100 messages"

    Args:
        percent: Decimal percentage (e.g., 0.25 for 25%)

    Returns:
        Human-readable fraction string
    """
    percent = math.floor(percent * 100) / 100

    if percent > 0.01:
        ans = findnum(str(percent))
        return "{} out of {} messages".format(int(percent * ans), int(1 * ans))
    else:
        return "<1 out of 100 messages"
