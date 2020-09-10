# Brock Palen
# brockp@umich.edu
# 7/2020
#
# purge files using mpiFileUtils drm optionally blow away empty folders

import argparse
import logging
import os
import pathlib
import sys

from dotenv import find_dotenv, load_dotenv

from mpiFileUtils import DRm


def parse_args(args):
    """CLI options takes sys.argv[1:]."""

    parser = argparse.ArgumentParser(
        description="Un-Archive a directory prepped by archivetar",
        epilog="Brock Palen brockp@umich.edu",
    )
    parser.add_argument(
        "--dryrun", help="Print what would do but dont do it", action="store_true"
    )
    parser.add_argument(
        "--purge-list",
        help="File created by --save-purge-list generated by archivetar",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--save-purge-list",
        help="Don't remove purge list when complete",
        action="store_true",
    )
    parser.add_argument(
        "--keep-empty-dirs", help="Don't remove empty directories", action="store_true"
    )

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        help="Increase messages, including files as added",
        action="store_true",
    )
    verbosity.add_argument(
        "-q", "--quiet", help="Decrease messages", action="store_true"
    )

    args = parser.parse_args(args)
    return args


def purge_empty_folders(path):
    """Rcurssively remove empty folders"""
    if not isinstance(path, pathlib.Path):
        # make pathlib
        path = pathlib.Path(path)

    if not path.is_dir():
        # path isn't a directory
        logging.debug(f"{path} is not a directory returning")
        return

    # remove empty sudir
    for f in path.iterdir():
        if f.is_dir():
            purge_empty_folders(f)

    # remove folders if empty
    # have to check path again count items in it
    entries = path.iterdir()
    if len(list(entries)) == 0:
        logging.debug(f"Removing emptry {path}")
        path.rmdir()


def main(argv):
    args = parse_args(argv[1:])
    if args.quiet:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # load in config from .env
    load_dotenv(find_dotenv(), verbose=args.verbose)

    # check if cachefile given exists
    purge_list = pathlib.Path(args.purge_list)
    if not purge_list.is_file():
        logging.critical(f"{purge_list} does not exist or not a file")
        sys.exit(-2)

    # setup drm

    drm_kwargs = {}
    if args.dryrun:
        drm_kwargs["dryrun"] = True

    drm = DRm(
        inst=os.getenv("AT_MPIFILEUTILS", default="/home/brockp/mpifileutils/install"),
        mpirun=os.getenv(
            "AT_MPIRUN",
            default="/sw/arcts/centos7/stacks/gcc/8.2.0/openmpi/4.0.3/bin/mpirun",
        ),
        progress="10",
        verbose=args.verbose,
        **drm_kwargs,
    )

    drm.scancache(cachein=purge_list)

    if args.dryrun:
        logging.debug("Dryrun requested exiting")
        sys.exit(0)

    # remove empty directories if requsted
    if args.keep_empty_dirs:
        logging.debug("Skipping removing empty directories")
    else:
        logging.debug("Removing empty directories")
        purge_empty_folders(pathlib.Path.cwd())

    # remove purge list unless requsted
    if not args.save_purge_list:
        logging.debug("Removing purge list")
        purge_list.unlink()
