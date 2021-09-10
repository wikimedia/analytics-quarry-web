# Use official python base image, small and debian edition
FROM amd64/python:3.7.3-slim

ARG purpose=dev

# Update debian packages
RUN apt-get update && \
    apt-get upgrade -y

# Create Quarry user, create /results folder owned by this user,
# to be mounted as volume to be shared between web and runner
RUN useradd -r -m quarry && \
    mkdir /results && \
    chown -R quarry: /results

WORKDIR /app

COPY requirements.txt /app
# Install python or test dependencies
RUN if [ ${purpose} = "test" ] ; then apt-get install -y tox redis-server; \
    else pip install --upgrade pip wheel && \
    pip install -r requirements.txt; fi

# Copy app code
USER quarry
COPY . /app

# Run web server
EXPOSE 5000
ENTRYPOINT ["python", "quarry.wsgi"]
