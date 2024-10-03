import argparse
from argparse import ArgumentTypeError
from pathlib import Path
from typing import Literal


class PathType(object):
    def __init__(
        self,
        exists: bool = True,
        type: Literal["file", "dir", "symlink"] | None = "file",
    ):
        """exists:
             True: a path that does exist
             False: a path that does not exist, in a valid parent directory
             None: don't care, in a valid parent directory
        type: file, dir, symlink, None, or a function returning True for valid paths
             None: don't care
        dash_ok: whether to allow - as stdin/stdout
        abs: if True, path will be coerced to an absolute path"""

        assert exists in (True, False, None)
        assert type in ("file", "dir", "symlink", None)

        self._exists: bool | None = exists
        self._type: Literal["file", "dir", "symlink"] | None = type

    def __call__(self, value) -> Path:
        if value == "-":
            # the special argument "-" means sys.std{in,out}
            raise ArgumentTypeError("standard input/output (-) not allowed")
        else:
            np = Path(value).resolve(False)
            if self._exists is True:
                if not np.exists():
                    raise ArgumentTypeError("path does not exist: '%s'" % np)

                if self._type is None:
                    pass
                elif self._type == "file":
                    if not np.is_file():
                        raise ArgumentTypeError("path is not a file: '%s'" % np)
                elif self._type == "symlink":
                    if not np.is_symlink():
                        raise ArgumentTypeError("path is not a symlink: '%s'" % np)
                elif self._type == "dir":
                    if not np.is_dir():
                        raise ArgumentTypeError("path is not a directory: '%s'" % np)
            else:
                if self._exists is False and np.exists():
                    raise ArgumentTypeError("path exists: '%s'" % np)

                p = np.parent
                if not p.is_dir():
                    raise ArgumentTypeError("parent path is not a directory: '%s'" % p)
                elif not p.exists():
                    raise ArgumentTypeError("parent directory does not exist: '%s'" % p)

        return np


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-i --intrface",
        dest="wg_iface",
        type=str,
        default="wg0",
        help="WireGuard interface name",
    )
    parser.add_argument(
        "-w --wg-config",
        dest="wg_config_dir",
        type=PathType(True, "dir"),
        default="/etc/wireguard",
        help="WireGuard config path",
    )
    parser.add_argument(
        "-k --wg-key",
        dest="wg_key_file",
        type=str,
        default=argparse.SUPPRESS,
        help='WireGuard private key file name (default: <ifname>-key)',
    )
    parser.add_argument(
        "-n --dry-run",
        dest="dry_run",
        default=False,
        action='store_true',
        help='Make no changes',
    )
    return parser
