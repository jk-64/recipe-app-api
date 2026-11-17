#!/bin/sh

# Force the script to stop if any command fails
set -e

# envsubst: environment substitute value
envsubst \
    < /etc/nginx/default.conf.tpl \
    > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'