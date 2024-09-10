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
#COPY ../poetry.lock pyproject.toml ./
#COPY README.md .
#
#RUN poetry check
#RUN poetry install --no-interaction --no-cache --no-root
#
#COPY .. .
#
#RUN chmod 755 .
#RUN echo "Europe/Moscow" > /etc/timezone && \
#    dpkg-reconfigure -f noninteractive tzdata
#
#CMD ["poetry", "run", "python", "-m", "bot"]


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

RUN apt-get update && apt-get install -y git

ENV USER=Guf-Hub
ENV REPO=sb_bot_new
ENV BRANCH=main
ENV GIT_HOME=/app

ADD https://api.github.com/repos/$USER/$REPO/git/refs/heads/$BRANCH version.json
RUN rm -rf /app/* && git clone -b $BRANCH https://github.com/$USER/$REPO.git $GIT_HOME

RUN poetry check \
    && poetry install --no-interaction --no-cache --no-root

RUN chmod 755 . \
    && echo "Europe/Moscow" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata

CMD ["poetry", "run", "python", "-m", "bot"]