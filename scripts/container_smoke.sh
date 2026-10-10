#!/usr/bin/env sh
set -eu

image="$1"
platform="$2"

docker buildx build --platform "$platform" --load --tag "$image" .
docker run --rm --platform "$platform" "$image" --version
docker run --rm --platform "$platform" "$image" diagnose
set +e
invalid_output="$(docker run --rm --platform "$platform" -e CMT_LOG_LEVEL=invalid "$image" diagnose 2>&1)"
invalid_status="$?"
set -e
if [ "$invalid_status" -ne 2 ]; then
  echo "invalid configuration exited $invalid_status, expected 2" >&2
  exit 1
fi
printf '%s\n' "$invalid_output" | grep -q '"event":"config.invalid"'
printf '%s\n' "$invalid_output" | grep -q '"error_category":"configuration"'
uid="$(docker run --rm --platform "$platform" --entrypoint id "$image" -u)"
test "$uid" != "0"
python3 scripts/catalog_smoke.py --mode docker --image "$image" --platform "$platform" --fixtures tests/fixtures
python3 scripts/observation_persistence_smoke.py --mode docker --image "$image" --platform "$platform" --fixtures tests/fixtures
echo "$platform smoke PASS; uid=$uid"
