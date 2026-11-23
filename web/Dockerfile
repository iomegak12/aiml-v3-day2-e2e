# syntax=docker/dockerfile:1
# NetCore TAC ETA — web UI image: NGINX (non-root) serving the static site and proxying the API.
# Build context: day2/  (compose: build.context=., dockerfile=web/Dockerfile)
# Context allow-list: web/Dockerfile.dockerignore

FROM nginxinc/nginx-unprivileged:1.30.6-alpine

ENV NGINX_ENTRYPOINT_QUIET_LOGS=1

COPY web/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY web/nginx/security-headers.conf web/nginx/proxy.conf /etc/nginx/snippets/
COPY web/site/ /usr/share/nginx/html/
COPY README.md /usr/share/nginx/html/README.md

# Fail the build on a config error (the API upstream is a variable, so it isn't resolved here)
RUN nginx -t

USER 101
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --start-interval=2s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
