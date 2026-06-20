# Python verson - alpine version (tag name)
FROM python:3.9-alpine3.13

# Define the maintainer. Best practice to know who develops
LABEL maintainer="jk"

# Recommanded when we run python in a container.
# PYTHONUNBUFFERED says to python that we don't buffer the output.
# The output from python will directly goes to the console and
# prevent any delays of messages getting from the running application
# to the screen. This permit to see the logs immediatly.
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app

# The WORKDIR is use to run the commands on the Docker image.
# It is set to the Django's project location. This permit to avoid
# running the full path to Django Management Commands
WORKDIR /app

# This expose the port:8000 from the container to the local machine.
# We use this port to connect to the Django Dev Server.
EXPOSE 8000

# RUN to add dependencies on the machine.
# By doing all in one RUN, we avoid creating several layer
# that help Docker to run the container faster.

# 1- create virtual environment to avoid any risk: python -m env /py
# 2- Full path of the virt. env: /py/bin/pip install --upgrade pip
# 3- Instal the requirement file in the docker image:
#       /py/bin/pip install -r /tmp/requirements.txt
# 4- Remove the tmp directory to avoid any dependencies in our image
#   once it has been created. The create smaller image.
# 5- BEST PRACTICE TO AVOID USING A ROOT USER: adduser
#               NEVER RUN THE APP USING THE ROOT USER
#               TO AVOID FULL ACCESS TO THE CONTAINER
# 6- No possibilities to login using a password: --disabled-password
# 7- No home dir for the user: --no-create-home
# 8- User's name: django-adduser
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-adduser

# Update the environment variable inside the image.
# $PATH is an automatically created env. variable on Linux systems.
# This define the directories where executables can be found.
# The commands are directly from the virtual env. by adding: /py/bin
ENV PATH="/py/bin:$PATH"

# This line should be the last line of the Dockerfile.
# It specifies the user to swithch to.
#          ALL LINES ABOVE ARE RUN BY THE ROOT USE.
USER django-user


###########################
# Specify a list of file that the Docker Context will ignore.
# This exclude any file that Docker doesn't need.
# The entries in this file are that most people uses.

# Git
.git
.gitignore

# Docker
# An hidden file that may be created in the project that contains
# specific info for Docker to work on the local machine.
.docker

# Python
# Removing __pycache__ may avoid error due to saved context from
# local machine that may not be compatible with the alpine image.
# We use /*/*... because .dockergitignore does not support /**/
app/__pycache__/
app/*/__pycache__/
app/*/*/__pycache__/
app/*/*/*/__pycache__/
.env/
.venv/
venv/