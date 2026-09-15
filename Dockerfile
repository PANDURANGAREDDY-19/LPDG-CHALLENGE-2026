FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data_selection.py dataset_inclusion.py model.py validate_submission.py ./

CMD ["python", "model.py", "--data", "/app/data", "--out", "/app/data/predictions.csv"]
