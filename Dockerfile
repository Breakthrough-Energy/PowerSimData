FROM python:3.8.3

RUN apt-get update && apt-get install -y pipenv

WORKDIR /app
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --dev --system; \
    pip install ipython;

COPY . .
RUN pip install .

CMD ["ipython"]
