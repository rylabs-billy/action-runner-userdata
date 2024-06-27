# base image
FROM alpine:3.20

# update package manager and install dependencies
RUN apk add --no-cache \
    bash \
    jq \
    github-cli \
    cloud-init

# copy source file required for the action
COPY entrypoint.sh /entrypoint.sh

# entrypoint for container execution
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]