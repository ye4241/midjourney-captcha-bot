FROM python:3
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
RUN playwright install --with-deps chromium
ENTRYPOINT ["python"]
CMD ["server.py"]