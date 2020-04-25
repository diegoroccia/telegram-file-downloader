FROM python:3.7

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN pip install poetry

RUN poetry config virtualenvs.create false 

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry install
