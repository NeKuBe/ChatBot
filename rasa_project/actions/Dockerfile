FROM rasa/rasa-sdk:latest
WORKDIR /app/actions
COPY actions.py /app/actions/actions.py
COPY __init__.py /app/actions/__init__.py
CMD ["python", "-m", "rasa_sdk", "--port", "5055"]
