FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV DB_HOST=localhost
ENV DB_NAME=meal_planner
ENV DB_USER=postgres
ENV DB_PASSWORD=password
ENV DB_PORT=5432

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
