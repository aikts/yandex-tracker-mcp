#syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:latest as uv

FROM python:3.13-slim as base

ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

ARG UV_INDEX_URL=${PIP_INDEX_URL}
ARG UV_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ARG UV_INDEX_STRATEGY=unsafe-best-match

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/code \
    PATH=/root/.local/bin:${PATH}

COPY --from=uv /uv /bin/uv

WORKDIR /code

FROM base as builder

ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

ARG UV_INDEX_URL=${PIP_INDEX_URL}
ARG UV_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}
ARG UV_INDEX_STRATEGY=unsafe-best-match

COPY pyproject.toml uv.lock /code/
ENV PATH=/venv/bin:$PATH
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN uv venv /venv && UV_PROJECT_ENVIRONMENT=/venv uv sync --locked

FROM base as final
ENV PATH=/venv/bin:$PATH
COPY --from=builder /venv /venv
COPY . .
RUN adduser --system --no-create-home nonroot
USER nonroot
ENTRYPOINT ["python", "-m", "mcp_tracker"]
