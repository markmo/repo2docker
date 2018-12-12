import argparse
import sys
import os
import docker
from .app import Repo2Docker
from . import __version__
from .utils import validate_and_generate_port_mapping

def validate_image_name(image_name):
    """
    Validate image_name read by argparse

    Note: Container names must start with an alphanumeric character and
    can then use _ . or - in addition to alphanumeric.
    [a-zA-Z0-9][a-zA-Z0-9_.-]+

    Args:
        image_name (string): argument read by the argument parser

    Returns:
        unmodified image_name

    Raises:
        ArgumentTypeError: if image_name contains characters that do not
                            meet the logic that container names must start
                            with an alphanumeric character and can then
                            use _ . or - in addition to alphanumeric.
                            [a-zA-Z0-9][a-zA-Z0-9_.-]+
    """
    if not is_valid_docker_image_name(image_name):
        msg = ("%r is not a valid docker image name. Image name"
                "must start with an alphanumeric character and"
                "can then use _ . or - in addition to alphanumeric." % image_name)
        raise argparse.ArgumentTypeError(msg)
    return image_name

def get_argparser():
    """Get arguments that may be used by repo2docker"""
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        '--config',
        default='repo2docker_config.py',
        help="Path to config file for repo2docker"
    )

    argparser.add_argument(
        '--json-logs',
        default=False,
        action='store_true',
        help='Emit JSON logs instead of human readable logs'
    )

    argparser.add_argument(
        'repo',
        help=('Path to repository that should be built. Could be '
                'local path or a git URL.')
    )

    argparser.add_argument(
        '--image-name',
        help=('Name of image to be built. If unspecified will be '
                'autogenerated'),
        type=validate_image_name
    )

    argparser.add_argument(
        '--ref',
        help=('If building a git url, which reference to check out. '
                'E.g., `master`.')
    )

    argparser.add_argument(
        '--debug',
        help="Turn on debug logging",
        action='store_true',
    )

    argparser.add_argument(
        '--no-build',
        dest='build',
        action='store_false',
        help=('Do not actually build the image. Useful in conjunction '
                'with --debug.')
    )

    argparser.add_argument(
        '--build-memory-limit',
        help='Total Memory that can be used by the docker build process'
    )

    argparser.add_argument(
        'cmd',
        nargs=argparse.REMAINDER,
        help='Custom command to run after building container'
    )

    argparser.add_argument(
        '--no-run',
        dest='run',
        action='store_false',
        help='Do not run container after it has been built'
    )

    argparser.add_argument(
        '--publish', '-p',
        dest='ports',
        action='append',
        help=('Specify port mappings for the image. Needs a command to '
                'run in the container.')
    )

    argparser.add_argument(
        '--publish-all', '-P',
        dest='all_ports',
        action='store_true',
        help='Publish all exposed ports to random host ports.'
    )

    argparser.add_argument(
        '--no-clean',
        dest='clean',
        action='store_false',
        help="Don't clean up remote checkouts after we are done"
    )

    argparser.add_argument(
        '--push',
        dest='push',
        action='store_true',
        help='Push docker image to repository'
    )

    argparser.add_argument(
        '--volume', '-v',
        dest='volumes',
        action='append',
        help='Volumes to mount inside the container, in form src:dest',
        default=[]
    )

    argparser.add_argument(
        '--user-id',
        help='User ID of the primary user in the image',
        type=int
    )

    argparser.add_argument(
        '--user-name',
        help='Username of the primary user in the image',
    )

    argparser.add_argument(
        '--env', '-e',
        dest='environment',
        action='append',
        help='Environment variables to define at container run time',
        default=[]
    )

    argparser.add_argument(
        '--editable', '-E',
        dest='editable',
        action='store_true',
        help='Use the local repository in edit mode',
    )

    argparser.add_argument(
        '--appendix',
        type=str,
        #help=self.traits()['appendix'].help,
    )

    argparser.add_argument(
        '--subdir',
        type=str,
        #help=self.traits()['subdir'].help,
    )

    argparser.add_argument(
        '--version',
        dest='version',
        action='store_true',
        help='Print the repo2docker version and exit.'
    )

    argparser.add_argument(
        '--cache-from',
        action='append',
        default=[],
        #help=self.traits()['cache_from'].help
    )

    return argparser


def make_r2d(argv=None):
    if argv is None:
        argv = sys.argv[1:]


    # version must be checked before parse, as repo/cmd are required and
    # will spit out an error if allowed to be parsed first.
    if '--version' in argv:
        print(__version__)
        sys.exit(0)

    args = get_argparser().parse_args(argv)

    r2d = Repo2Docker()

    if args.debug:
        r2d.log_level = logging.DEBUG

    r2d.load_config_file(args.config)
    if args.appendix:
        r2d.appendix = args.appendix

    r2d.repo = args.repo
    r2d.ref = args.ref

    # user wants to mount a local directory into the container for
    # editing
    if args.editable:
        # the user has to point at a directory, not just a path for us
        # to be able to mount it. We might have content providers that can
        # provide content from a local `something.zip` file, which we
        # couldn't mount in editable mode
        if os.path.isdir(args.repo):
            r2d.volumes[os.path.abspath(args.repo)] = '.'
        else:
            r2d.log.error('Can not mount "{}" in editable mode '
                            'as it is not a directory'.format(args.repo),
                            extra=dict(phase='failed'))
            sys.exit(1)


    if args.image_name:
        r2d.output_image_spec = args.image_name

    r2d.json_logs = args.json_logs

    r2d.dry_run = not args.build

    if r2d.dry_run:
        # Can't push nor run if we aren't building
        args.run = False
        args.push = False

    r2d.run = args.run
    r2d.push = args.push

    # check against r2d.run and not args.run as r2d.run is false on
    # --no-build
    if args.volumes and not r2d.run:
        # Can't mount if we aren't running
        print('To Mount volumes with -v, you also need to run the '
                'container')
        sys.exit(1)

    for v in args.volumes:
        src, dest = v.split(':')
        r2d.volumes[src] = dest

    r2d.run_cmd = args.cmd

    if args.all_ports and not r2d.run:
        print('To publish user defined port mappings, the container must '
                'also be run')
        sys.exit(1)

    if args.ports and not r2d.run:
        print('To publish user defined port mappings, the container must '
                'also be run')
        sys.exit(1)

    if args.ports and not r2d.run_cmd:
        print('To publish user defined port mapping, user must specify '
                'the command to run in the container')
        sys.exit(1)

    r2d.ports = validate_and_generate_port_mapping(args.ports)
    r2d.all_ports = args.all_ports

    if args.user_id:
        r2d.user_id = args.user_id
    if args.user_name:
        r2d.user_name = args.user_name

    if args.build_memory_limit:
        r2d.build_memory_limit = args.build_memory_limit

    if args.environment and not r2d.run:
        print('To specify environment variables, you also need to run '
                'the container')
        sys.exit(1)

    if args.subdir:
        r2d.subdir = args.subdir

    if args.cache_from:
        r2d.cache_from = args.cache_from

    r2d.environment = args.environment

    # if the source exists locally we don't want to delete it at the end
    if os.path.exists(args.repo):
        r2d.cleanup_checkout = False
    else:
        r2d.cleanup_checkout = args.clean

    return r2d


def main():
    r2d = make_r2d()
    r2d.initialize()
    try:
        r2d.start()
    except docker.errors.BuildError as e:
        # This is only raised by us
        if r2d.debug:
            r2d.log.exception(e)
        sys.exit(1)
    except docker.errors.ImageLoadError as e:
        # This is only raised by us
        if r2d.debug:
            r2d.log.exception(e)
        sys.exit(1)

if __name__ == '__main__':
    main()
