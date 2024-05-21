FROM python:3.12

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN pip install poetry

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

RUN npm install fullcalendar

COPY . /app/


RUN poetry run black . --line-length 120
