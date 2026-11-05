import pandas as pd, pytest
from model import table_store as TS

@pytest.fixture
def env(tmp_path, monkeypatch):
    base = tmp_path / "data"; base.mkdir()
    pd.DataFrame({"Age": [1, 2, 3], "q": [0.1, 0.2, 0.3]}).to_csv(base / "t.csv", index=False)
    (base / "manifest.json").write_text("{}")
    monkeypatch.setattr(TS, "BASE", base); monkeypatch.setattr(TS, "USER", tmp_path / "data_user")
    return base

def test_default_uses_base(env):
    assert not TS.is_customised() and TS.effective_dir() == TS.BASE

def test_save_and_reset(env):
    new = TS.load("t"); new.loc[3] = [4, 0.4]
    TS.save("t", new)
    assert TS.is_customised() and len(TS.load("t")) == 4 and len(TS.load("t", original=True)) == 3
    TS.reset("t"); assert len(TS.load("t")) == 3
    TS.reset(); assert not TS.is_customised()

def test_original_untouched(env):
    new = TS.load("t"); new["q"] = 0.5; TS.save("t", new)
    assert TS.load("t", original=True)["q"].tolist() == [0.1, 0.2, 0.3]

@pytest.mark.parametrize("mut,msg", [
    (lambda d: d.rename(columns={"q": "x"}), "cannot be removed"),
    (lambda d: d.assign(Age=[1, 1, 3]), "unique"),
    (lambda d: d.assign(Age=[3, 2, 1]), "increasing"),
    (lambda d: d.assign(q=["a", 0.2, 0.3]), "numeric"),
    (lambda d: d.iloc[0:0], "empty"),
])
def test_validation(env, mut, msg):
    errs = TS.validate("t", mut(TS.load("t")))
    assert errs and msg in errs[0]
    with pytest.raises(ValueError): TS.save("t", mut(TS.load("t")))

def test_backup_made(env):
    d = TS.load("t"); TS.save("t", d); TS.save("t", d)
    assert list((TS.USER / "backups").glob("t_*.csv"))

def test_add_and_drop_column(env):
    TS.add_column("t", "note", "text", "hi")
    d = TS.load("t"); assert d["note"].tolist() == ["hi"] * 3 and TS.extra_columns("t") == ["note"]
    TS.add_column("t", "adj", "number", "1.5"); assert TS.load("t")["adj"].tolist() == [1.5] * 3
    TS.drop_column("t", "note"); assert "note" not in TS.load("t")
    assert TS.load("t", original=True).columns.tolist() == ["Age", "q"]

def test_column_guards(env):
    with pytest.raises(ValueError): TS.add_column("t", "q")
    with pytest.raises(ValueError): TS.add_column("t", "  ")
    TS.add_column("t", "n", "text")
    with pytest.raises(ValueError): TS.drop_column("t", "q")
