# Golden cases

Each file in `cases/` is a client scenario (only values that differ from the model defaults are listed).
`expected/` holds the saved Python results for those cases. They are created with `UPDATE_GOLDEN=1 pytest -m golden`
and are committed to git. A failing golden test means a number changed: either fix the code, or, if the change is
intended, regenerate the file and review `git diff tests/golden/expected` before committing.

Because only overrides are stored, a change to a default input (for example InflationLoad) changes every case.
That is intentional: it makes default changes visible.
