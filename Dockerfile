# syntax=docker/dockerfile:1
FROM python:3.14.6-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR $APP_HOME

# Install dependencies first so layer caching helps during rebuilds.
COPY requirements.txt $APP_HOME/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . $APP_HOME/

# Create a non-root user to run the application.
RUN groupadd -r kniffel && useradd -r -g kniffel kniffel \
    && mkdir -p $APP_HOME/data /home/kniffel \
    && chown -R kniffel:kniffel $APP_HOME /home/kniffel
USER kniffel

# Expose the Gunicorn port.
EXPOSE 8000

# Run migrations and start the server.
CMD ["/app/docker-entrypoint.sh"]
