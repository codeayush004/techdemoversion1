# Simple Python Runner
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install flask
COPY . .
CMD ["python", "app.py"]
