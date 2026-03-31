from __future__ import annotations

from app.ml.dataset import MODEL_FEATURES, build_spend_dataset
from app.ml.predict import predict_single, predict_spend


def main() -> None:
    df = build_spend_dataset()

    sample_df = df[MODEL_FEATURES].sample(5)
    preds = predict_spend(sample_df)

    print("Batch predictions:")
    for i, pred in enumerate(preds, start=1):
        print(f"Row {i}: {pred:.2f}")

    single_row = df[MODEL_FEATURES].iloc[0].to_dict()
    single_pred = predict_single(single_row)

    print("\nSingle prediction:")
    print(f"{single_pred:.2f}")


if __name__ == "__main__":
    main()