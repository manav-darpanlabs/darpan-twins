import argparse
import os
from typing import List, Tuple

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def build_synthetic_dataset() -> pd.DataFrame:
    # Minimal seed phrases per Likert 1..5
    seed = {
        1: ["I dislike this.", "This feels wrong for me.", "Definitely not a match."],
        2: ["I'm not into it.", "Probably skip.", "Doesn't fit my needs."],
        3: ["I'm unsure.", "Could go either way.", "Neutral about it."],
        4: ["I like this.", "Sounds good to me.", "I'd consider it."],
        5: ["I love this.", "Absolutely yes.", "Perfect for me."],
    }
    rows = []
    for k, phrases in seed.items():
        for t in phrases:
            rows.append({"text": t, "label": k})
    return pd.DataFrame(rows)


def train_pipeline(out_dir: str) -> None:
    df = build_synthetic_dataset()
    n = len(df)
    n_classes = df["label"].nunique()
    # Ensure at least one sample per class in the test split when stratifying
    test_size = max(n_classes, int(round(0.2 * n)))
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=test_size,
        random_state=123,
        stratify=df["label"],
    )
    pipe = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, multi_class="multinomial")),
        ]
    )
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    print(classification_report(y_test, y_pred, digits=3))
    os.makedirs(out_dir, exist_ok=True)
    joblib.dump(pipe, os.path.join(out_dir, "likert_pipeline.pkl"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a simple Likert classifier for 1–5 on short texts")
    parser.add_argument("--model_dir", type=str, default="models")
    args = parser.parse_args()
    train_pipeline(args.model_dir)


if __name__ == "__main__":
    main()


