FROM python:3.12-slim
WORKDIR /app
COPY peis-production-substrate/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY peis-production-substrate /app/peis-production-substrate
COPY peis-persistence-reference /app/peis-persistence-reference
COPY peis-service-bridge-reference /app/peis-service-bridge-reference
COPY peis-reference-kernel /app/peis-reference-kernel
COPY 277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json 285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json /app/
EXPOSE 8080
CMD ["python", "/app/peis-production-substrate/runtime.py"]
