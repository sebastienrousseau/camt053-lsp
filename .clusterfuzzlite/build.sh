#!/bin/bash -eu
# ClusterFuzzLite build script: install the package and compile every
# fuzz/fuzz_*.py harness into a libFuzzer binary placed in $OUT.

pip3 install .

for harness in "$SRC"/camt053-lsp/fuzz/fuzz_*.py; do
  name="$(basename "$harness" .py)"
  compile_python_fuzzer "$harness" --name "$name"
done
