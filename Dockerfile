FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
# CPU-only torch keeps the image far smaller than the default CUDA build
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu .
CMD ["uvicorn", "docqa.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
