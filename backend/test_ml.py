from app.ml.dataset import build_spend_dataset, MODEL_FEATURES

df = build_spend_dataset(num_users=20)

print("Shape:", df.shape)
print(df.head())
print("\nFeatures:")
print(df[MODEL_FEATURES].head())