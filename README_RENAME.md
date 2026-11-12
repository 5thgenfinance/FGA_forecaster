# Input naming refactor: how to install

Goal: replace the old input names (p_dob, t_ret_date, LTRoR, ...) with the standard ones (primary_dob,
primary_target_ret_date, lt_return_rate, ...). The mapping lives in **`model/input_names.json`** (old name -> new name).
`model/legacy_names.py` loads it; `tools/rename_inputs.py` reads the same file. Edit the JSON, not the code.

## Before you start
1. Make the golden tests pass and commit the saved results (`tests/golden/expected`). They prove the rename changes no numbers.
2. `git add -A` and `git commit -m "baseline before rename"`.

## Install
1. Unzip over the project. New files: `model/input_names.json`, `model/legacy_names.py`, `tools/rename_inputs.py`,
   `tests/test_legacy_names.py`, `tests/test_naming_post_refactor.py`. Commit them too (the tool needs a clean git tree).
2. Dry run (changes nothing):  `python tools/rename_inputs.py`
   Read the "Review these" list. Files with parity, export or workbook in the name keep their strings (they may be Excel names).
3. Apply:  `python tools/rename_inputs.py --apply`
   The tool compiles every edited file and rolls the Python edits back if any fails.
4. Run the tests:  `python -m pytest -m "not parity"`  and then the parity tests.
   Golden and rule tests must give identical numbers. `test_naming_post_refactor.py` should now pass.
   The parity tests should be exactly as they were before (same pass or fail status).

## Changing a name later
Edit `model/input_names.json` (old name on the left, new on the right; no new name may also be an old name) and run
the tool again. `test_legacy_names.py` fails if the file is malformed, has two old names with one new name, or a non-snake_case new name.

## Two edits the tool cannot make for you
* `client_io.parse_import`: accept client files saved before the rename. After the JSON is loaded, add
  `from model.legacy_names import migrate_inputs` and `data["inputs"] = migrate_inputs(data["inputs"])`.
  New files are written with the new names. Old files are renamed on import.
* Anything that reads Excel defined names into ProjectionInputs (the parity and export code): the workbook still uses the
  old names, so wrap the dict, e.g. `ProjectionInputs(**migrate_inputs(values_from_workbook))`.

## If something goes wrong
`git checkout .` restores everything the tool changed (JSON files too), because you committed first.
