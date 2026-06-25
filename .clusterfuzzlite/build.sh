#!/bin/bash -eu
# ClusterFuzzLite build script: install the package and compile every
# fuzz/fuzz_*.py harness into a libFuzzer binary placed in $OUT.
# compile_python_fuzzer derives the fuzzer name from the file basename.
#
# --collect-data camt053 bundles camt053's non-Python data files (the JSON
# schemas and XSDs loaded at runtime) into the frozen PyInstaller binary;
# without them schema-backed entry points raise FileNotFoundError on startup.

pip3 install .

for harness in "$SRC"/camt053-lsp/fuzz/fuzz_*.py; do
  compile_python_fuzzer "$harness" --collect-data camt053
done
