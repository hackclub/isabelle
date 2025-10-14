FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN apt update
RUN apt install -y curl

RUN uv python install
RUN uv sync --frozen

# Run piccolo migrations on the database
RUN piccolo migrations forwards isabelle
RUN piccolo migrations forwards session_auth
RUN piccolo migrations forwards user


EXPOSE 3000

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "main.py"]