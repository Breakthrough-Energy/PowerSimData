FROM python:3.8.3

RUN apt-get update
RUN apt-get install gawk
RUN ln -s /mnt/bes/pcm $HOME/ScenarioData

COPY powersimdata/utility/templates /mnt/bes/pcm/

WORKDIR /app
COPY Pipfile .
COPY Pipfile.lock .
RUN pip install -U pip pipenv ipython; \
    pipenv sync --dev --system; \
    pip install jedi==0.17.2

COPY . .
RUN pip install .

CMD ["ipython"]
