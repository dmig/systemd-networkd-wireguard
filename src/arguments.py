import argparse
import ipaddress
from pathlib import Path
from typing import Literal

DEFAULT_ADDR = "10.0.0.1/24"


class PathType:
    def __init__(
        self,
        exists: bool = True,
        type: Literal["file", "dir", "symlink"] | None = "file",
    ):
        """
        :param exists:
             True: a path that does exist
             False: a path that does not exist, in a valid parent directory
             None: don't care, in a valid parent directory
        :param type: file, dir, symlink, None, or a function returning True for valid paths
             None: don't care
        """

        assert exists in (True, False, None)
        assert type in ("file", "dir", "symlink", None)

        self._exists: bool | None = exists
        self._type: Literal["file", "dir", "symlink"] | None = type

    def __call__(self, value) -> Path:
        if value == "-":
            # the special argument "-" means sys.std{in,out}
            raise argparse.ArgumentTypeError("standard input/output (-) not allowed")
        else:
            np = Path(value).resolve(False)
            if self._exists is True:
                if not np.exists():
                    raise argparse.ArgumentTypeError(f"path does not exist: '{np}'")

                if self._type is None:
                    pass
                elif self._type == "file" and not np.is_file():
                    raise argparse.ArgumentTypeError(f"path is not a file: '{np}'")
                elif self._type == "symlink" and not np.is_symlink():
                    raise argparse.ArgumentTypeError(f"path is not a symlink: '{np}'")
                elif self._type == "dir" and not np.is_dir():
                    raise argparse.ArgumentTypeError(f"path is not a directory: '{np}'")
            else:
                if self._exists is False and np.exists():
                    raise argparse.ArgumentTypeError(f"path exists: '{np}'")

                p = np.parent
                if not p.is_dir():
                    raise argparse.ArgumentTypeError(
                        f"parent path is not a directory: '{p}'"
                    )
                elif not p.exists():
                    raise argparse.ArgumentTypeError(
                        f"parent directory does not exist: '{p}'"
                    )

        return np


class SubstitutingArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **(
                kwargs
                | dict(
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                    epilog="NOTE: %s in paramters will be substituted with interface name",
                )
            ),
        )

    def add_base_arguments(self):
        self.add_argument("interface", type=str, help="Wireguard interface name")
        self.add_argument(
            "-n, --dry-run",
            dest="dry_run",
            default=False,
            action="store_true",
            help="Make no changes",
        )
        self.add_argument(
            "-v, --verbose",
            dest="verbose",
            default=False,
            action="store_true",
        )

    def add_path_arguments(self):
        self.add_argument(
            "--networkd-config-dir",
            type=PathType(True, "dir"),
            default="/etc/systemd/network/",
            help="Networkd config path",
        )
        self.add_argument(
            "--networkd-config-prefix",
            type=str,
            default="wireguard-%s",
            help="Networkd .netdev and .network files prefix",
        )
        self.add_key_dir_argument()

    def add_key_dir_argument(self):
        self.add_argument(
            "--key-dir",
            type=PathType(True, "dir"),
            default="/etc/wireguard",
            help="Wireguard key files directory",
        )

    def parse_args(self, args=None, namespace=None):
        ns = super().parse_args(args, namespace)
        ifname: str = ns.interface
        args = vars(ns)
        for key in args:
            v = args[key]
            if isinstance(v, str) and "%s" in v:
                args[key] = v % (ifname,)

        return argparse.Namespace(**args)


def get_peer_argparser(description: str | None = None) -> SubstitutingArgumentParser:
    parser = SubstitutingArgumentParser(description=description)
    parser.add_base_arguments()
    parser.add_path_arguments()
    parser.add_argument(
        "--peer-key-prefix",
        type=str,
        default="%s-peer-",
        help="Peer key file names prefix",
    )

    subparsers = parser.add_subparsers(help="Action to perform")

    subparsers.add_parser("list", help="list all configured peers")

    command2 = subparsers.add_parser("set", help="add or edit configured peer")
    command2.add_argument("name", help="Peer name, part of key file name after prefix")

    command3 = subparsers.add_parser("remove", help="remove peer")
    command3.add_argument("name", help="Peer name, part of key file name after prefix")

    command4 = subparsers.add_parser("export", help="export peer config")
    command4.add_argument("name", help="Peer name, part of key file name after prefix")

    return parser


def get_netdev_argparser(description: str | None = None) -> SubstitutingArgumentParser:
    parser = SubstitutingArgumentParser(description=description)
    parser.add_base_arguments()
    parser.add_argument(
        "--description",
        type=str,
        default="Wireguard interface - %s",
        help="Interface description",
    )
    parser.add_path_arguments()
    parser.add_argument(
        "--private-key-file",
        type=str,
        default="%s.key",
        help="Wireguard private key file name",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=argparse.SUPPRESS,
        help="Wireguard UDP port for listening (default: autoassigned by Networkd)",
        required=False,
    )
    parser.add_argument(
        "--network",
        type=ipaddress.ip_network,
        default=argparse.SUPPRESS,
        action="append",
        help="A static IPv4 or IPv6 address and its prefix length, separated by a '/' character. "
        f"This option may be specified more than once. (default: {DEFAULT_ADDR})",
    )
    parser.add_argument(
        "--dns",
        type=ipaddress.ip_network,
        default=argparse.SUPPRESS,
        action="append",
        help="A DNS server address, which must be in the format described in inet_pton(3). "
        "This option may be specified more than once. "
        "See more: https://freedesktop.org/software/systemd/man/latest/systemd.network.html#DNS=",
    )
    parser.add_argument(
        "--mtu-size",
        type=int,
        default=argparse.SUPPRESS,
        help="Wireguard interface MTU value (default: auto)",
        required=False,
    )
    parser.add_argument(
        "--ip-masquerade",
        choices=("ipv4", "ipv6", "both", "no"),
        default="both",
        help="Enable masquerade if the server is expected to be used as a gateway to the Internet."
        "Set to 'no' to tonfi",
    )
    parser.add_argument(
        "--force-new",
        default=False,
        action="store_true",
        help="Ignore existing configuration files.",
    )

    return parser

def get_keys_argparser(description: str | None = None) -> SubstitutingArgumentParser:
    parser = SubstitutingArgumentParser(description=description)
    parser.add_base_arguments()
    parser.add_key_dir_argument()
    parser.add_argument(
        "--private-key-file",
        type=str,
        default="%s.key",
        help="Wireguard private key file name",
    )

    return parser
