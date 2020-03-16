ARG ALPINE_VERSION=3.9.4
FROM alpine:${ALPINE_VERSION}

RUN apk add --no-cache git python3 python3-dev

# build wheels in first image
ADD . /tmp/src
# restore the hooks directory so that the repository isn't marked as dirty
RUN cd /tmp/src && git clean -xfd && git checkout -- hooks && git status
RUN mkdir /tmp/wheelhouse \
 && cd /tmp/wheelhouse \
 && pip3 install wheel \
 && pip3 wheel --no-cache-dir /tmp/src \
 && ls -l /tmp/wheelhouse

FROM alpine:${ALPINE_VERSION}

# install python, git, bash
RUN apk add --no-cache git git-lfs python3 bash openssh-client

# install repo2docker
COPY --from=0 /tmp/wheelhouse /tmp/wheelhouse
RUN pip3 install --no-cache-dir /tmp/wheelhouse/*.whl \
 && pip3 list

# add git-credential helper
COPY ./docker/git-credential-env /usr/local/bin/git-credential-env
RUN git config --system credential.helper env

ARG SSH_PRIVATE_KEY
RUN mkdir /root/.ssh
RUN echo "${SSH_PRIVATE_KEY}" > /root/.ssh/id_rsa
RUN chmod 400 /root/.ssh/id_rsa

RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts

# Used for testing purpose in ports.py
EXPOSE 52000
