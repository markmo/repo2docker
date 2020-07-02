Docker image layers:

1. Dockerfile.base
2. Templated base.py


Dockerfile.base (based on Ubuntu 18.04.4 LTS)

As root:
    1. Set env as noninteractive
    2. Setup locales
    3. apt installs
    4. kubectl install
    5. args and node env settings
    6. gcloud install
    7. garden install
    8. notebook user env settings and notebook user creation
    9. conda env settings and miniconda install
    10. europa api install
    11. jupyter-proxy server install
    12. autocommit service install
    13. git scripts

As jovyan (notebook user):
    14. theia install
    15 set path (node_modules/bin)
