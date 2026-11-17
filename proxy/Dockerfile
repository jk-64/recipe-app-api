# Call a base image "nginx-unprivileged" with the version "1-alpine"
FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer='aran.drillconsult.com'

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

# We set the ENVIRONMENT VARIABLES that are defined
# in "/etc/nginx/default.conf.tpl"
# REM: All those variables can be overriden at run-time.
ENV LISTEN_PORT=8000
# The host name where is running the server uWSGI
ENV APP_HOST=app
ENV APP_PORT=9000

# The script switch to the root user to RUN
# the commands manipulating the file system.
USER root

RUN mkdir -p /vol/static && \
    chmod 755 /vol/static && \
    touch /etc/nginx/conf.d/default.conf && \
    # To be able the override the content of file when nginx user \
    # runs the command "envsubst" defined in: proxy > run.sh \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

# Default volume created for the NGINX image
VOLUME /vol/static

USER nginx

CMD ["/run.sh"]