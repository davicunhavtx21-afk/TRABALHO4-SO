FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN groupadd --system --gid 10001 appgrp \
    && useradd --system --uid 10001 --gid appgrp --no-create-home --shell /usr/sbin/nologin appuser
WORKDIR /app
COPY --chown=root:root --chmod=0644 app/app.py /app/app.py
USER appuser
EXPOSE 8080
CMD ["python", "/app/app.py"]
