FROM ghcr.io/astral-sh/uv:0.12.10@sha256:2bb3ebca0a796a155094a27773d290c4b074572e6107f171d88d086682fd2500 AS uv

FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c AS build
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --frozen --no-install-project \
    && uv build --no-build-isolation --wheel --out-dir /wheels \
    && uv venv --python /usr/local/bin/python3 /app/runtime \
    && uv pip install --python /app/runtime/bin/python --no-deps /wheels/*.whl

FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c
RUN groupadd --gid 10001 cmt && useradd --uid 10001 --gid 10001 --create-home cmt \
    && install -d -m 0700 -o 10001 -g 10001 /data
WORKDIR /app
COPY --from=build /app/runtime /app/runtime
ENV PATH="/app/runtime/bin:$PATH" CMT_WORK_DIR=/tmp
USER 10001:10001
ENTRYPOINT ["cmt"]
CMD ["diagnose"]
