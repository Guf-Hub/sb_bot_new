#FROM python:3.12-slim
#
#WORKDIR /app
#COPY requirements.txt requirements.txt
#RUN pip install --upgrade pip
#RUN pip install --upgrade setuptools
#RUN pip install -r requirements.txt
#
#RUN chmod 755 .
#COPY . .
#
#CMD ["python", "bot.py"]

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
#COPY ../poetry.lock pyproject.toml ./
#COPY README.md .
#
#RUN poetry check
#RUN poetry install --no-interaction --no-cache --no-root
#
##COPY ../.. .
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
COPY ../poetry.lock pyproject.toml ./
COPY README.md .

RUN git init \
    && git remote add origin https://github.com/Guf-Hub/git.git \
    && git fetch --all \
    && git reset --hard origin/master

RUN poetry check \
    && poetry install --no-interaction --no-cache --no-root

#COPY ../.. .
COPY .. .

RUN chmod 755 . \
    && echo "Europe/Moscow" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata

CMD ["poetry", "run", "python", "-m", "bot"]