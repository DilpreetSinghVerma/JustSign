FROM openjdk:11.0.9.1-jre

COPY --from=python:3.7.7-stretch / /

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

RUN python nltk_downloader.py

CMD ["python", "run.py"]
