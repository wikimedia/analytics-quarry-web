# Use official python base image, small and debian edition
FROM python:3.7.11-slim

# Update debian packages
RUN apt-get update && \
    apt-get upgrade -y

# Create Quarry user, create /results folder owned by this user,
# to be mounted as volume to be shared between web and runner
RUN useradd -r -m quarry && \
    mkdir /results && \
    chown -R quarry: /results

WORKDIR /app

# Install python dependencies
COPY requirements.txt /app
RUN pip install --upgrade pip wheel && \
    pip install -r requirements.txt

# Copy app code
USER quarry
COPY . /app

# Run web server
EXPOSE 5000
ENTRYPOINT ["python", "quarry.wsgi"]
