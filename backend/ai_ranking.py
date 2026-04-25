import time
import math


# 🔥 RECENCY (time decay)
def recency_score(last_opened):
    if not last_opened:
        return 0

    now = time.time()
    diff_days = (now - last_opened.timestamp()) / (60 * 60 * 24)

    return math.exp(-diff_days / 7)  # decay over 7 days


    # 🔥 FREQUENCY
def frequency_score(open_count):
    return min(math.log1p(open_count) / 3, 1)


# 🔥 NEGLECT (ignored files)
def neglect_penalty(open_count, days_unused):
    if open_count == 0 and days_unused > 30:
        return 0.5
    return 0


    # 🔥 FINAL ADAPTIVE AI SCORE
def adaptive_importance(content_score, filename_score, open_count, last_opened):

    rec = recency_score(last_opened)
    freq = frequency_score(open_count)

    days_unused = 999
    if last_opened:
        days_unused = (time.time() - last_opened.timestamp()) / (60*60*24)

        penalty = neglect_penalty(open_count, days_unused)

        score = (
            0.45 * content_score +
            0.25 * freq +
            0.20 * rec +
            0.10 * filename_score
        )

        score = score * (1 - penalty)

        return round(min(score, 1), 2)