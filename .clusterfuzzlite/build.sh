#!/bin/bash -eu
# ClusterFuzzLite build script: install the package and compile every
# fuzz/fuzz_*.py harness into a libFuzzer binary placed in $OUT.
# compile_python_fuzzer derives the fuzzer name from the file basename.

pip3 install .

for harness in "$SRC"/camt053-lsp/fuzz/fuzz_*.py; do
  compile_python_fuzzer "$harness"
done
