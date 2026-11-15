from sklearn.model_selection import train_test_split

# Keep this block importable by pytest outside Mage.
try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(func):
        return func
    def test(func):
        return func


@transformer
def transform(df, *args, **kwargs):
    train_idx, test_idx = train_test_split(
        df.index, test_size=0.2, random_state=42, stratify=df["target"]
    )
    out = df.copy()
    out["split"] = "train"
    out.loc[test_idx, "split"] = "test"
    return out


@test
def test_split(output, *args):
    assert (output["split"] == "train").sum() == 120
    assert (output["split"] == "test").sum() == 30
