FROM python:3.12-slim AS python-base

ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv

ENV POETRY_CACHE_DIR=/opt/.cache

FROM python-base AS poetry-base

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

FROM python-base AS app

COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app
COPY ../poetry.lock pyproject.toml ./
COPY README.md .

RUN poetry check
RUN poetry install --no-interaction --no-cache --no-root

#COPY ../.. .
COPY .. .

RUN chmod 755 .
RUN echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

CMD ["poetry", "run", "python", "-m", "bot"]

#
#FROM python:3.12-slim AS python-base
#
#ENV POETRY_VERSION=1.8.3
#ENV POETRY_HOME=/opt/poetry
#ENV POETRY_VENV=/opt/poetry-venv
#
#ENV POETRY_CACHE_DIR=/opt/.cache
#
#FROM python-base AS poetry-base
#
#RUN python3 -m venv $POETRY_VENV \
#    && $POETRY_VENV/bin/pip install -U pip setuptools \
#    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}
#
#FROM python-base AS app
#
#COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}
#ENV PATH="${PATH}:${POETRY_VENV}/bin"
#
#WORKDIR /app
#
#RUN apt-get update && apt-get install -y git
#RUN git clone https://github.com/Guf-Hub/sb_bot_new.git .
#
#RUN poetry check \
#    && poetry install --no-interaction --no-cache --no-root
#
#RUN chmod 755 . \
#    && echo "Europe/Moscow" > /etc/timezone \
#    && dpkg-reconfigure -f noninteractive tzdata
#
#CMD ["poetry", "run", "python", "-m", "bot"]