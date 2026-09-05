# oml-tools

Command-line tooling for the Open Misconception Library. Python 3.10+,
`jsonschema` is the only dependency.

```sh
pip install -e tools/oml
oml validate records/          # schema + cross-record checks; non-zero exit on error
oml index                      # regenerate records/INDEX.md
oml export case|jsonl|csv|all  # write dist/
oml build-site                 # write site/ (static HTML + JSON)
```

Run the tests from the repo root with `python -m unittest discover -s tools/tests`.
