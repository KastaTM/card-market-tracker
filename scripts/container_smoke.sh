#!/usr/bin/env sh
set -eu

image="$1"
platform="$2"

docker buildx build --platform "$platform" --load --tag "$image" .
docker run --rm --platform "$platform" "$image" --version
docker run --rm --platform "$platform" "$image" diagnose
if docker run --rm --platform "$platform" -e CMT_LOG_LEVEL=invalid "$image" diagnose; then
  echo "invalid configuration unexpectedly succeeded" >&2
  exit 1
fi
uid="$(docker run --rm --platform "$platform" --entrypoint id "$image" -u)"
test "$uid" != "0"
echo "$platform smoke PASS; uid=$uid"
