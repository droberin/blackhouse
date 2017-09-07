FROM python:3-slim
RUN mkdir -p /app/etc && mkdir /app/blackhouse
WORKDIR /app
ADD requirements.txt /app/
RUN pip3 install -r requirements.txt
COPY blackhouse /app/blackhouse
COPY docker-entrypoint.py /app
COPY docker-entrypoint-pizero-switch-server.py /app
COPY examples/configs/*.example /app/etc/
CMD /usr/local/bin/python3 docker-entrypoint.py

EXPOSE 5000 5001
