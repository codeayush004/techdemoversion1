FROM python:latest
ENV DB_PASSWORD="password123"
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD python app.py
