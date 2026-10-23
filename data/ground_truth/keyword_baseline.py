
# Keyword baseline for NAC_2026 complaints (30-sample evaluation)
# Target accuracy: 70-75% on complaints_30.csv
# This baseline uses Arabic keywords; more advanced rules can be added.

def classify_complaint(description_ar: str) -> str:
    desc_lower = description_ar.lower()
    scores = {}
    for category, words in keywords.items():
        scores[category] = sum(1 for w in words if w in desc_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unknown"

def evaluate_baseline(csv_path: str = "data/complaints_30.csv", key_path: str = "data/complaints_30_key.csv") -> float:
    import pandas as pd
    df = pd.read_csv(csv_path)
    key_df = pd.read_csv(key_path)
    correct = 0
    for _, row in df.iterrows():
        pred = classify_complaint(row["description_ar"])
        true_cat = key_df[key_df["complaint_id"] == row["complaint_id"]]["true_category"].values
        if len(true_cat) > 0 and pred == true_cat[0]:
            correct += 1
    total = len(df)
    accuracy = correct / total if total > 0 else 0.0
    return accuracy, correct, total

if __name__ == "__main__":
    acc, c, t = evaluate_baseline()
    print(f"Keyword baseline accuracy: {acc:.2%} ({c}/{t} correct)")
    # Expected: 70-75% (21-23/30 correct with 6 categories, 30 stratified)
