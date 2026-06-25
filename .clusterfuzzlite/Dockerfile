# ClusterFuzzLite build image for camt053-lsp (Python / Atheris).
# Used by the .github/workflows/cflite-*.yml workflows to build the fuzz
# targets in fuzz/ against the OSS-Fuzz Python base image.
FROM gcr.io/oss-fuzz-base/base-builder-python

COPY . $SRC/camt053-lsp
WORKDIR $SRC/camt053-lsp
COPY .clusterfuzzlite/build.sh $SRC/build.sh
