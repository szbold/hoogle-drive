FROM python:3.13-alpine

RUN mkdir /.hoogle

WORKDIR /hoogle-server

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["fastapi", "run", "src/main.py", "--port", "8080"]

