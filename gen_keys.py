import os
from pathlib import Path
from subprocess import check_output
import sys
from src.arguments import get_argparser

if __name__ == '__main__':
    parser = get_argparser()
    args = parser.parse_args()

    if 'wg_key_file' not in args:
        args.wg_key_file = args.wg_iface + '-key'

    pk: Path = args.wg_config_dir / args.wg_key_file
    if not os.access(pk if pk.exists() else pk.parent, os.W_OK):
        print(f'Key file {pk} is not writable, exiting.', file=sys.stderr)
        sys.exit(os.EX_NOPERM)

    priv_key = check_output(['wg', 'genkey'])
    pk.write_bytes(priv_key)
    pk = pk.with_suffix('.pub')
    public_key = check_output(['wg', 'pubkey'], input=priv_key)
    pk.write_bytes(public_key)
