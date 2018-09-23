.. _install:

Installing ``repo2docker``
==========================

repo2docker requires Python 3.4 and above on Linux and macOS. See
:ref:`below <windows>` for more information about Windows support.

Prerequisite: Docker
--------------------

Install `Docker <https://www.docker.com>`_ as it is required
to build Docker images. The
`Community Edition <https://www.docker.com/community-edition>`_,
is available for free.

Recent versions of Docker are recommended.
The latest version of Docker, ``18.03``, successfully builds repositories from
`binder-examples <https://github.com/binder-examples>`_.
The `BinderHub <https://binderhub.readthedocs.io/>`_ helm chart uses version
``17.11.0-ce-dind``.  See the
`helm chart <https://github.com/jupyterhub/binderhub/blob/master/helm-chart/binderhub/values.yaml#L167>`_
for more details.

Installing with ``pip``
-----------------------

We recommend installing ``repo2docker`` with the ``pip`` tool::

    python3 -m pip install jupyter-repo2docker

For information on using ``repo2docker``, see :ref:`usage`.

Installing from source code
---------------------------

Alternatively, you can install repo2docker from source,
i.e. if you are contributing back to this project::

  git clone https://github.com/jupyter/repo2docker.git
  cd repo2docker
  pip install -e .

That's it! For information on using ``repo2docker``, see
:ref:`usage`.

.. _windows:

Windows support
---------------

Windows support for ``repo2docker`` is still in the experimental stage.

An article about `using Windows and the WSL`_ (Windows Subsytem for Linux or
Bash on Windows) provides additional information about Windows and docker.


.. _using Windows and the WSL: https://nickjanetakis.com/blog/setting-up-docker-for-windows-and-wsl-to-work-flawlessly
