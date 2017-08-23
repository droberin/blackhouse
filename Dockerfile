FROM python:3-slim
RUN mkdir /app
WORKDIR /app
ADD . /app/
ADD requirements.txt /app/
RUN pip3 install -r requirements.txt
CMD /usr/local/bin/python3 docker-entrypoint.py
