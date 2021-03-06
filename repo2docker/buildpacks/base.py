import textwrap
import jinja2
import tarfile
import io
import os
import re
import logging
import string
import sys
import hashlib
import escapism
import xml.etree.ElementTree as ET

from traitlets import Dict

TEMPLATE = r"""
# FROM buildpack-deps:bionic

# # avoid prompts from apt
# ENV DEBIAN_FRONTEND=noninteractive

# # Set up locales properly
# RUN apt-get -qq update && \
#     apt-get -qq install --yes --no-install-recommends locales git rsync curl vim > /dev/null && \
#     apt-get -qq purge && \
#     apt-get -qq clean && \
#     rm -rf /var/lib/apt/lists/*

# RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
#     locale-gen
FROM localhost:5000/repo2docker-garden-base:0.0.25

USER root

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# # Install kubectl
# RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.14.10/bin/linux/amd64/kubectl && \
#     chmod +x ./kubectl && \
#     mv ./kubectl /usr/local/bin/kubectl

# Set up user
ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

# Use bash as default shell, rather than sh

# TODO
# Secure setting
# but causing `/bin/sh: 5: /etc/profile.d/activate-conda.sh: [[: not found`
# when opening a terminal in Jupyter Lab, therefore using bash below
# RUN chsh -s /bin/rbash ${NB_USER}

# RUN chattr +i /home/${NB_USER}/.bashrc
# ENV SHELL /bin/rbash

ENV SHELL /bin/bash

# RUN groupadd \
#         --gid ${NB_UID} \
#         ${NB_USER} && \
#     useradd \
#         --comment "Default user" \
#         --create-home \
#         --gid ${NB_UID} \
#         --no-log-init \
#         --shell /bin/bash \
#         --uid ${NB_UID} \
#         ${NB_USER}

# RUN wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key |  apt-key add - && \
#     DISTRO="bionic" && \
#     echo "deb https://deb.nodesource.com/node_10.x $DISTRO main" >> /etc/apt/sources.list.d/nodesource.list && \
#     echo "deb-src https://deb.nodesource.com/node_10.x $DISTRO main" >> /etc/apt/sources.list.d/nodesource.list

# Base package installs are not super interesting to users, so hide their outputs
# If install fails for some reason, errors will still be printed
{% if base_packages -%}
RUN apt-get -qq update && \
    apt-get -qq install --yes --no-install-recommends \
       {% for package in base_packages -%}
       {{ package }} \
       {% endfor -%}
    > /dev/null && \
    apt-get -qq purge && \
    apt-get -qq clean && \
    rm -rf /var/lib/apt/lists/*
{% endif -%}

{% if packages -%}
RUN apt-get -qq update && \
    apt-get -qq install --yes \
       {% for package in packages -%}
       {{ package }} \
       {% endfor -%}
    > /dev/null && \
    apt-get -qq purge && \
    apt-get -qq clean && \
    rm -rf /var/lib/apt/lists/*
{% endif -%}

# # tool to watch for file changes
# RUN apt-get -qq update && \
#     apt-get -qq install --yes inotify-tools \
#     > /dev/null && \
#     apt-get -qq purge && \
#     apt-get -qq clean && \
#     rm -rf /var/lib/apt/lists/*

EXPOSE 8888

{% if build_env -%}
# Environment variables required for build
{% for item in build_env -%}
ENV {{item[0]}} {{item[1]}}
{% endfor -%}
{% endif -%}

{% if path -%}
# Special case PATH
ENV PATH {{ ':'.join(path) }}:${PATH}
{% endif -%}

{% if build_script_files -%}
# If scripts required during build are present, copy them
{% for src, dst in build_script_files|dictsort %}
COPY {{ src }} {{ dst }}
{% endfor -%}
{% endif -%}

{% for sd in build_script_directives -%}
{{sd}}
{% endfor %}

# Allow target path repo is cloned to be configurable
ARG REPO_DIR=${HOME}
ENV REPO_DIR ${REPO_DIR}
WORKDIR ${REPO_DIR}

# We want to allow two things:
#   1. If there's a .local/bin directory in the repo, things there
#      should automatically be in path
#   2. postBuild and users should be able to install things into ~/.local/bin
#      and have them be automatically in path
#
# The XDG standard suggests ~/.local/bin as the path for local user-specific
# installs. See https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
ENV PATH ${HOME}/.local/bin:${REPO_DIR}/.local/bin:${PATH}

{% if env -%}
# The rest of the environment
{% for item in env -%}
ENV {{item[0]}} {{item[1]}}
{% endfor -%}
{% endif -%}

# Run pre-assemble scripts! These are instructions that depend on the content
# of the repository but don't access any files in the repository. By executing
# them before copying the repository itself we can cache these steps. For
# example installing APT packages.
{% if preassemble_script_files -%}
# If scripts required during build are present, copy them
{% for src, dst in preassemble_script_files|dictsort %}
COPY src/{{ src }} ${REPO_DIR}/{{ dst }}
{% endfor -%}
{% endif -%}

{% if preassemble_script_directives -%}
USER root
RUN chown -R ${NB_USER}:${NB_USER} ${REPO_DIR}
{% endif -%}

{% for sd in preassemble_script_directives -%}
{{ sd }}
{% endfor %}

# Copy and chown stuff. This doubles the size of the repo, because
# you can't actually copy as USER, only as root! Thanks, Docker!
USER root
COPY src/ ${REPO_DIR}
RUN chown -R ${NB_USER}:${NB_USER} ${REPO_DIR} && \
    mkdir -p /home/$NB_USER/.jupyter && \
    chown -R ${NB_USER}:${NB_USER} /home/$NB_USER/.jupyter

## TODO causing "chown: changing ownership of '/home/jovyan/garden.yml': Operation not permitted"
# COPY /garden.yml /home/$NB_USER/garden.yml
# RUN chown $NB_USER:$NB_USER /home/$NB_USER/garden.yml

# Run assemble scripts! These will actually turn the specification
# in the repository into an image.
{% for sd in assemble_script_directives -%}
{{ sd }}
{% endfor %}

# Container image Labels!
# Put these at the end, since we don't want to rebuild everything
# when these change! Did I mention I hate Dockerfile cache semantics?
{% for k, v in labels|dictsort %}
LABEL {{k}}="{{v}}"
{%- endfor %}

# # Add Jupyter Notebook config
# COPY /jupyter_notebook_config.py /home/$NB_USER/.jupyter/jupyter_notebook_config.py

# # Install autocommit service
# COPY /autocommit.sh /home/$NB_USER/autocommit.sh
# RUN mkdir -p /home/$NB_USER/.config/systemd/user
# COPY /autocommit.service /home/$NB_USER/.config/systemd/user/autocommit.service
# # RUN chmod 644 /home/$NB_USER/.config/systemd/user/autocommit.service

# # Add scripts
# COPY /fetch.sh /home/$NB_USER/fetch.sh
# COPY /merge.sh /home/$NB_USER/merge.sh

# # Install Europa
# COPY /europa/ /home/$NB_USER/europa/
# RUN python3 -m pip install Flask flask-cors gevent gevent-ws
# COPY /europa.service /home/$NB_USER/.config/systemd/user/europa.service

# # Install Theia
# RUN npm install -g yarn
# COPY /package.json /home/$NB_USER/package.json

# WORKDIR /home/$NB_USER
# # Next version of theia-full does not build https://github.com/theia-ide/theia-apps/issues/371
# RUN yarn install --network-timeout 100000 && \
#     yarn theia build
# ENV PATH "/home/$NB_USER/node_modules/.bin:${PATH}"

# RUN pip install jupyter-server-proxy
COPY /garden.yml /home/$NB_USER/garden.yml
RUN chown $NB_USER:$NB_USER /home/$NB_USER/garden.yml

# We always want containers to run as non-root
USER ${NB_USER}

{% if post_build_scripts -%}
# Make sure that postBuild scripts are marked executable before executing them
{% for s in post_build_scripts -%}
RUN chmod +x {{ s }}
RUN ./{{ s }}
{% endfor %}
{% endif -%}

# Add start script
{% if start_script is not none -%}
RUN chmod +x "{{ start_script }}"
ENV R2D_ENTRYPOINT "{{ start_script }}"
{% endif -%}

# Append ignore files
# {% if ignore_files -%}
# {% for item in ignore_files -%}
# RUN echo "{{item}}" >> .gitignore
# {% endfor -%}
# {% endif -%}

# # Install GCloud
# # TODO
# COPY /apt-phenomenon-243802-bbe918a2d411.json /home/$NB_USER/apt-phenomenon-243802-bbe918a2d411.json

# ENV GCLOUD_SERVICE_KEY /home/$NB_USER/apt-phenomenon-243802-bbe918a2d411.json
# ENV GOOGLE_PROJECT_ID apt-phenomenon-243802
# ENV GOOGLE_COMPUTE_ZONE us-central1-b

# RUN mkdir /home/$NB_USER/gcloud && \
#     curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz | tar xvz -C /home/$NB_USER/gcloud && \
#     /home/$NB_USER/gcloud/google-cloud-sdk/install.sh --quiet && \
#     /home/jovyan/gcloud/google-cloud-sdk/bin/gcloud auth activate-service-account notebook-container@apt-phenomenon-243802.iam.gserviceaccount.com --key-file=/home/$NB_USER/apt-phenomenon-243802-bbe918a2d411.json --project=apt-phenomenon-243802 && \
#     # shows warning for unknown reason
#     /home/jovyan/gcloud/google-cloud-sdk/bin/gcloud config set project apt-phenomenon-243802 && \
#     /home/jovyan/gcloud/google-cloud-sdk/bin/gcloud config set compute/zone us-central1-b

# # Install Garden
# RUN curl -sL https://get.garden.io/install.sh | bash

# RUN echo 'export PATH=$HOME/gcloud/google-cloud-sdk/bin:$HOME/.garden/bin:$PATH' >> /home/$NB_USER/.bashrc

# COPY /kubeconfig.yml /home/$NB_USER/.kube/config

# COPY /create_kube_account.sh /home/$NB_USER/create_kube_account.sh

# COPY /garden.yml /home/$NB_USER/garden.yml

ENV GARDEN_SERVER_PORT 9777
ENV GARDEN_DISABLE_ANALYTICS true

RUN bentoml config set yatai_service.url=https://yatai.devsheds.io:50051

WORKDIR ${REPO_DIR}

# see https://community.theia-ide.org/t/need-help-updating-theia-core-and-deploying-it-to-a-docker-container/648/20
# https://github.com/eclipse-theia/theia/blob/fc49b2c3b8a690ba5b94e1fd48cf17469b51057d/packages/plugin-ext/src/main/common/webview-protocol.ts#L17-L27
# https://github.com/eclipse-theia/theia/blob/cf86e86857c45ab82366508cd270d217d6d66b04/packages/plugin-ext/src/main/browser/webview/webview-environment.ts#L33

RUN git config --global user.email "jovyan@europanb.com"
RUN git config --global user.name "europanb"

ARG GIT_BRANCH
ENV GIT_BRANCH ${GIT_BRANCH}
# ENV PYTHONPATH /home/${NB_USER}/europa:$PYTHONPATH
# TODO update for prod
# fails to connect (yet I can from within the pod)
# 0.0.0.0:9004 failed as well
# maybe related to insecure (http) endpoint
# ENV THEIA_WEBVIEW_EXTERNAL_ENDPOINT localhost:9004
# 404
# ENV THEIA_WEBVIEW_EXTERNAL_ENDPOINT jupyterhub.europanb.online
# ENV THEIA_WEBVIEW_EXTERNAL_ENDPOINT app.europanb.online/jupyterhub

# Add entrypoint
COPY /repo2docker-entrypoint /usr/local/bin/repo2docker-entrypoint
ENTRYPOINT ["/usr/local/bin/repo2docker-entrypoint"]

# Specify the default command to run
CMD ["jupyter", "notebook", "--ip", "0.0.0.0"]

{% if appendix -%}
# Appendix:
{{ appendix }}
{% endif %}
"""

ENTRYPOINT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "repo2docker-entrypoint"
)

NOTEBOOK_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "jupyter_notebook_config.py"
)

PACKAGE_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "package.json"
)

AUTOCOMMIT_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "autocommit.sh"
)

POST_START_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fetch.sh"
)

PRE_STOP_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "merge.sh"
)

EUROPA_APP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "europa"
)

GARDEN_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "garden.yml"
)

KUBECONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "kubeconfig.yml"
)

CREATE_KUBE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "create_kube_account.sh"
)

KEY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "apt-phenomenon-243802-bbe918a2d411.json"
)

AUTOCOMMIT_SERVICE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "autocommit.service"
)

EUROPA_SERVICE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "europa.service"
)


class BuildPack:
    """
    A composable BuildPack.

    Specifically used for creating Dockerfiles for use with repo2docker only.

    Things that are kept constant:
     - base image
     - some environment variables (such as locale)
     - user creation & ownership of home directory
     - working directory

    Everything that is configurable is additive & deduplicative,
    and there are *some* general guarantees of ordering.

    """

    def __init__(self):
        self.log = logging.getLogger("repo2docker")
        self.appendix = ""
        self.labels = {}
        if sys.platform.startswith("win"):
            self.log.warning(
                "Windows environment detected. Note that Windows "
                "support is experimental in repo2docker."
            )

    def get_packages(self):
        """
        List of packages that are installed in this BuildPack.

        Versions are not specified, and ordering is not guaranteed. These
        are usually installed as apt packages.
        """
        return set()

    def get_base_packages(self):
        """
        Base set of apt packages that are installed for all images.

        These contain useful images that are commonly used by a lot of images,
        where it would be useful to share a base docker image layer that
        contains them.

        These would be installed with a --no-install-recommends option.
        """
        return {
            # Utils!
            # "less",
            # "nodejs",
            # "unzip",
        }

    def get_build_env(self):
        """
        Ordered list of environment variables to be set for this image.

        Ordered so that environment variables can use other environment
        variables in their values.

        Expects tuples, with the first item being the environment variable
        name and the second item being the value.

        These environment variables will be set prior to build.
        Use .get_env() to set environment variables after build.
        """
        return []

    def get_env(self):
        """
        Ordered list of environment variables to be set for this image.

        Ordered so that environment variables can use other environment
        variables in their values.

        Expects tuples, with the first item being the environment variable
        name and the second item being the value.

        These variables will not be available to build.
        """
        return []

    def get_ignore_files(self):
        return []

    def get_path(self):
        """
        Ordered list of file system paths to look for executables in.

        Just sets the PATH environment variable. Separated out since
        it is very commonly set by various buildpacks.
        """
        return []

    def get_labels(self):
        """
        Docker labels to set on the built image.
        """
        return self.labels

    def get_build_script_files(self):
        """
        Dict of files to be copied to the container image for use in building.

        This is copied before the `build_scripts` & `assemble_scripts` are
        run, so can be executed from either of them.

        It's a dictionary where the key is the source file path in the host
        system, and the value is the destination file path inside the
        container image.
        """
        return {}

    @property
    def stencila_manifest_dir(self):
        """Find the stencila manifest dir if it exists"""
        if hasattr(self, "_stencila_manifest_dir"):
            return self._stencila_manifest_dir

        # look for a manifest.xml that suggests stencila could be used
        # when we find one, stencila should be installed
        # and set environment variables such that
        # this file is located at:
        # ${STENCILA_ARCHIVE_DIR}/${STENCILA_ARCHIVE}/manifest.xml

        self._stencila_manifest_dir = None

        for root, dirs, files in os.walk("."):
            if "manifest.xml" in files:
                self.log.debug("Found a manifest.xml at %s", root)
                self._stencila_manifest_dir = root.split(os.path.sep, 1)[1]
                self.log.info(
                    "Using stencila manifest.xml in %s", self._stencila_manifest_dir
                )
                break
        return self._stencila_manifest_dir

    @property
    def stencila_contexts(self):
        """Find the stencila manifest contexts from file path in manifest"""
        if hasattr(self, "_stencila_contexts"):
            return self._stencila_contexts

        # look at the content of the documents in the manifest
        # to extract the required execution contexts
        self._stencila_contexts = set()

        # get paths to the article files from manifest
        files = []
        if self.stencila_manifest_dir:
            manifest = ET.parse(
                os.path.join(self.stencila_manifest_dir, "manifest.xml")
            )
            documents = manifest.findall("./documents/document")
            files = [
                os.path.join(self.stencila_manifest_dir, x.get("path"))
                for x in documents
            ]

        else:
            return self._stencila_contexts

        for filename in files:
            self.log.debug("Extracting contexts from %s", filename)

            # extract code languages from file
            document = ET.parse(filename)
            code_chunks = document.findall('.//code[@specific-use="source"]')
            languages = [x.get("language") for x in code_chunks]
            self._stencila_contexts.update(languages)

            self.log.info(
                "Added executions contexts, now have %s", self._stencila_contexts
            )
            break

        return self._stencila_contexts

    def get_build_scripts(self):
        """
        Ordered list of shell script snippets to build the base image.

        A list of tuples, where the first item is a username & the
        second is a single logical line of a bash script that should
        be RUN as that user.

        These are run before the source of the repository is copied
        into the container image, and hence can not reference stuff
        from the repository. When the build scripts are done, the
        container image should be in a state where it is generically
        re-useable for building various other repositories with
        similar environments.

        You can use environment variable substitutions in both the
        username and the execution script.
        """

        return []

    def get_preassemble_script_files(self):
        """
        Dict of files to be copied to the container image for use in preassembly.

        This is copied before the `build_scripts`, `preassemble_scripts` and
        `assemble_scripts` are run, so can be executed from either of them.

        It's a dictionary where the key is the source file path in the
        repository and the value is the destination file path inside the
        repository in the container.
        """
        return {}

    def get_preassemble_scripts(self):
        """
        Ordered list of shell snippets to build an image for this repository.

        A list of tuples, where the first item is a username & the
        second is a single logical line of a bash script that should
        be RUN as that user.

        These are run before the source of the repository is copied into
        the container image. These should be the scripts that depend on the
        repository but do not need access to the contents.

        For example the list of APT packages to install.
        """
        return []

    def get_assemble_scripts(self):
        """
        Ordered list of shell script snippets to build the repo into the image.

        A list of tuples, where the first item is a username & the
        second is a single logical line of a bash script that should
        be RUN as that user.

        These are run after the source of the repository is copied into
        the container image (into the current directory). These should be
        the scripts that actually build the repository into the container
        image.

        If this needs to be dynamically determined (based on the presence
        or absence of certain files, for example), you can create any
        method and decorate it with `traitlets.default('assemble_scripts)`
        and the return value of this method is used as the value of
        assemble_scripts. You can expect that the script is running in
        the current directory of the repository being built when doing
        dynamic detection.

        You can use environment variable substitutions in both the
        username and the execution script.
        """
        return []

    def get_post_build_scripts(self):
        """
        An ordered list of executable scripts to execute after build.

        Is run as a non-root user, and must be executable. Used for performing
        build time steps that can not be performed with standard tools.

        The scripts should be as deterministic as possible - running it twice
        should not produce different results!
        """
        return []

    def get_start_script(self):
        """
        The path to a script to be executed at container start up.

        This script is added as the `ENTRYPOINT` to the container.

        It is run as a non-root user, and must be executable. Used for
        performing run time steps that can not be performed with standard
        tools. For example setting environment variables for your repository.

        The script should be as deterministic as possible - running it twice
        should not produce different results.
        """
        return None

    @property
    def binder_dir(self):
        has_binder = os.path.isdir("binder")
        has_dotbinder = os.path.isdir(".binder")

        if has_binder and has_dotbinder:
            raise RuntimeError(
                "The repository contains both a 'binder' and a '.binder' "
                "directory. However they are exclusive."
            )

        if has_dotbinder:
            return ".binder"
        elif has_binder:
            return "binder"
        else:
            return ""

    def binder_path(self, path):
        """Locate a file"""
        return os.path.join(self.binder_dir, path)

    def detect(self):
        return True

    def render(self, safe_mode):
        """
        Render BuildPack into Dockerfile
        """
        t = jinja2.Template(TEMPLATE)

        build_script_directives = []
        last_user = "root"
        for user, script in self.get_build_scripts():
            if last_user != user:
                build_script_directives.append("USER {}".format(user))
                last_user = user
            build_script_directives.append(
                "RUN {}".format(textwrap.dedent(script.strip("\n")))
            )

        assemble_script_directives = []
        last_user = "root"
        for user, script in self.get_assemble_scripts():
            if last_user != user:
                assemble_script_directives.append("USER {}".format(user))
                last_user = user
            assemble_script_directives.append(
                "RUN {}".format(textwrap.dedent(script.strip("\n")))
            )

        preassemble_script_directives = []
        last_user = "root"
        for user, script in self.get_preassemble_scripts():
            if last_user != user:
                preassemble_script_directives.append("USER {}".format(user))
                last_user = user
            preassemble_script_directives.append(
                "RUN {}".format(textwrap.dedent(script.strip("\n")))
            )

        # Based on a physical location of a build script on the host,
        # create a mapping between:
        #   1. Location of a build script in a Docker build context
        #      ('assemble_files/<escaped-file-path-truncated>-<6-chars-of-its-hash>')
        #   2. Location of the aforemention script in the Docker image
        # Base template basically does: COPY <1.> <2.>
        if safe_mode:
            build_script_files = {}
        else:
            build_script_files = {
                self.generate_build_context_filename(k)[0]: v
                for k, v in self.get_build_script_files().items()
            }

        return t.render(
            packages=sorted(self.get_packages()),
            path=self.get_path(),
            build_env=self.get_build_env(),
            env=self.get_env(),
            labels=self.get_labels(),
            build_script_directives=build_script_directives,
            preassemble_script_files=self.get_preassemble_script_files(),
            preassemble_script_directives=preassemble_script_directives,
            assemble_script_directives=assemble_script_directives,
            build_script_files=build_script_files,
            base_packages=sorted(self.get_base_packages()),
            post_build_scripts=self.get_post_build_scripts(),
            start_script=self.get_start_script(),
            appendix=self.appendix,
            ignore_files=self.get_ignore_files(),
        )

    @staticmethod
    def generate_build_context_filename(src_path, hash_length=6):
        """
        Generate a filename for a file injected into the Docker build context.

        In case the src_path is relative, it's assumed it's relative to directory of
        this __file__. Returns the resulting filename and an absolute path to the source
        file on host.
        """
        if not os.path.isabs(src_path):
            src_parts = src_path.split("/")
            src_path = os.path.join(os.path.dirname(__file__), *src_parts)

        src_path_hash = hashlib.sha256(src_path.encode("utf-8")).hexdigest()
        safe_chars = set(string.ascii_letters + string.digits)

        def escape(s):
            return escapism.escape(s, safe=safe_chars, escape_char="-")

        src_path_slug = escape(src_path)
        filename = "build_script_files/{name}-{hash}"
        return (
            filename.format(
                name=src_path_slug[: 255 - hash_length - 20],
                hash=src_path_hash[:hash_length],
            ).lower(),
            src_path,
        )

    def build(
        self,
        client,
        image_spec,
        memory_limit,
        build_args,
        cache_from,
        extra_build_kwargs,
        safe_mode,
    ):
        tarf = io.BytesIO()
        tar = tarfile.open(fileobj=tarf, mode="w")
        dockerfile_tarinfo = tarfile.TarInfo("Dockerfile")
        dockerfile = self.render(safe_mode).encode("utf-8")
        dockerfile_tarinfo.size = len(dockerfile)

        tar.addfile(dockerfile_tarinfo, io.BytesIO(dockerfile))

        def _filter_tar(tar):
            # We need to unset these for build_script_files we copy into tar
            # Otherwise they seem to vary each time, preventing effective use
            # of the cache!
            # https://github.com/docker/docker-py/pull/1582 is related
            tar.uname = ""
            tar.gname = ""
            tar.uid = int(build_args.get("NB_UID", 1000))
            tar.gid = int(build_args.get("NB_UID", 1000))
            return tar

        for src in sorted(self.get_build_script_files()):
            dest_path, src_path = self.generate_build_context_filename(src)
            tar.add(src_path, dest_path, filter=_filter_tar)

        tar.add(ENTRYPOINT_FILE, "repo2docker-entrypoint", filter=_filter_tar)
        tar.add(NOTEBOOK_CONFIG_FILE, "jupyter_notebook_config.py", filter=_filter_tar)
        tar.add(PACKAGE_JSON, "package.json", filter=_filter_tar)
        tar.add(AUTOCOMMIT_SCRIPT, "autocommit.sh", filter=_filter_tar)
        tar.add(POST_START_SCRIPT, "fetch.sh", filter=_filter_tar)
        tar.add(PRE_STOP_SCRIPT, "merge.sh", filter=_filter_tar)
        tar.add(GARDEN_FILE, "garden.yml", filter=_filter_tar)
        tar.add(KUBECONFIG_FILE, "kubeconfig.yml", filter=_filter_tar)
        tar.add(CREATE_KUBE_ACCOUNT_FILE, "create_kube_account.sh", filter=_filter_tar)
        # tar.add(KEY_FILE, "apt-phenomenon-243802-bbe918a2d411.json", filter=_filter_tar)
        tar.add(AUTOCOMMIT_SERVICE_FILE, "autocommit.service", filter=_filter_tar)
        tar.add(EUROPA_SERVICE_FILE, "europa.service", filter=_filter_tar)

        tar.add(".", "src/", filter=_filter_tar)
        tar.add(EUROPA_APP, "europa", filter=_filter_tar)

        tar.close()
        tarf.seek(0)

        # If you work on this bit of code check the corresponding code in
        # buildpacks/docker.py where it is duplicated
        if not isinstance(memory_limit, int):
            raise ValueError(
                "The memory limit has to be specified as an"
                "integer but is '{}'".format(type(memory_limit))
            )
        limits = {}
        if memory_limit:
            # We want to always disable swap. Docker expects `memswap` to
            # be total allowable memory, *including* swap - while `memory`
            # points to non-swap memory. We set both values to the same so
            # we use no swap.
            limits = {"memory": memory_limit, "memswap": memory_limit}

        build_kwargs = dict(
            fileobj=tarf,
            tag=image_spec,
            custom_context=True,
            buildargs=build_args,
            decode=True,
            forcerm=True,
            rm=True,
            container_limits=limits,
            cache_from=cache_from,
        )

        build_kwargs.update(extra_build_kwargs)

        for line in client.build(**build_kwargs):
            yield line


class BaseImage(BuildPack):

    def get_build_env(self):
        """Return env directives required for build"""
        return [
            # ("APP_BASE", "/srv"),
            # ("NPM_DIR", "${APP_BASE}/npm"),
            # ("NPM_CONFIG_GLOBALCONFIG", "${NPM_DIR}/npmrc"),
        ]

    def get_path(self):
        return super().get_path()# + ["${NPM_DIR}/bin"]

    def get_build_scripts(self):
        scripts = [
            # (
            #     "root",
            #     r"""
            #     mkdir -p ${NPM_DIR} && \
            #     chown -R ${NB_USER}:${NB_USER} ${NPM_DIR}
            #     """,
            # ),
            # (
            #     "${NB_USER}",
            #     r"""
            #     npm config --global set prefix ${NPM_DIR}
            #     """,
            # ),
        ]

        return super().get_build_scripts() + scripts

    def get_env(self):
        """Return env directives to be set after build"""
        env = []
        if self.stencila_manifest_dir:
            # manifest_dir is the path containing the manifest.xml
            # archive_dir is the directory containing archive directories
            # (one level up) default archive is the name of the directory
            # in the archive_dir such that
            # ${STENCILA_ARCHIVE_DIR}/${STENCILA_ARCHIVE}/manifest.xml
            # exists.

            archive_dir, archive = os.path.split(self.stencila_manifest_dir)
            env.extend(
                [
                    ("STENCILA_ARCHIVE_DIR", "${REPO_DIR}/" + archive_dir),
                    ("STENCILA_ARCHIVE", archive),
                ]
            )
        return env

    def get_ignore_files(self):
        ignore_files = [
            '.bash_logout',
            '.bashrc',
            '.config/',
            '.ipython/',
            '.jupyter/',
            '.local/',
            '.profile',
            '.gitconfig',
        ]
        return ignore_files

    def detect(self):
        return True

    def get_preassemble_scripts(self):
        scripts = []
        try:
            with open(self.binder_path("apt.txt")) as f:
                extra_apt_packages = []
                for l in f:
                    package = l.partition("#")[0].strip()
                    if not package:
                        continue
                    # Validate that this is, indeed, just a list of packages
                    # We're doing shell injection around here, gotta be careful.
                    # FIXME: Add support for specifying version numbers
                    if not re.match(r"^[a-z0-9.+-]+", package):
                        raise ValueError(
                            "Found invalid package name {} in "
                            "apt.txt".format(package)
                        )
                    extra_apt_packages.append(package)

            scripts.append(
                (
                    "root",
                    # This apt-get install is *not* quiet, since users explicitly asked for this
                    r"""
                apt-get -qq update && \
                apt-get install --yes --no-install-recommends {} && \
                apt-get -qq purge && \
                apt-get -qq clean && \
                rm -rf /var/lib/apt/lists/*
                """.format(
                        " ".join(sorted(extra_apt_packages))
                    ),
                )
            )

        except FileNotFoundError:
            pass

        if "py" in self.stencila_contexts:
            scripts.extend(
                [
                    (
                        "${NB_USER}",
                        r"""
                        ${KERNEL_PYTHON_PREFIX}/bin/pip install --no-cache https://github.com/stencila/py/archive/f1260796.tar.gz && \
                        ${KERNEL_PYTHON_PREFIX}/bin/python -m stencila register
                        """,
                    )
                ]
            )
        if self.stencila_manifest_dir:
            scripts.extend(
                [
                    (
                        "${NB_USER}",
                        r"""
                        ${NB_PYTHON_PREFIX}/bin/pip install --no-cache nbstencilaproxy==0.1.1 && \
                        jupyter serverextension enable --sys-prefix --py nbstencilaproxy && \
                        jupyter nbextension install    --sys-prefix --py nbstencilaproxy && \
                        jupyter nbextension enable     --sys-prefix --py nbstencilaproxy
                        """,
                    )
                ]
            )
        return scripts

    def get_assemble_scripts(self):
        """Return directives to run after the entire repository has been added to the image"""
        return []

    def get_post_build_scripts(self):
        post_build = self.binder_path("postBuild")
        if os.path.exists(post_build):
            return [post_build]
        return []

    def get_start_script(self):
        start = self.binder_path("start")
        if os.path.exists(start):
            # Return an absolute path to start
            # This is important when built container images start with
            # a working directory that is different from ${REPO_DIR}
            # This isn't a problem with anything else, since start is
            # the only path evaluated at container start time rather than build time
            return os.path.join("${REPO_DIR}", start)
        return None
