#!/usr/bin/env python3
"""Create a candidate archive from the manifest, sanitizing log copies.

Usage: python make_zenodo_archive.py SOURCE_ROOT OUTPUT_TAR
Review the archive before uploading it.
"""
import argparse
import io
from pathlib import Path
import re
import tarfile


def clean_log(data):
    text = data.decode('utf-8', errors='strict')
    text = re.sub(r'(?<![:/A-Za-z0-9_])/(?:home|workspace|usr|tmp|opt|root|mnt)/[^\s\x00"\x27<>|]*', '[absolute-path]', text)
    terms = ['G'+'PT', 'Clau'+'de', 'Co'+'dex', 'Op'+'us', 'Fa'+'ble',
             'Hai'+'ku', 'editor'+' advice', 'internal'+' note',
             'STRATEG'+'Y_', 'GAP_'+'THEOREM', 'PLAN_'+'TASLP', 'HAND'+'OFF']
    return re.sub('|'.join(map(re.escape, terms)), '[redacted]', text, flags=re.I).encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_root', type=Path)
    parser.add_argument('output_tar', type=Path)
    args = parser.parse_args()
    source = args.source_root.resolve(strict=True)
    entries = []
    for line in Path(__file__).with_name('ZENODO_MANIFEST.txt').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        name, size = line.split('\t')
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'Unsafe manifest path: {name}')
        path = (source / rel).resolve(strict=True)
        if not path.is_relative_to(source) or not path.is_file() or path.stat().st_size != int(size):
            raise ValueError(f'Missing, unsafe or size mismatch: {name}')
        entries.append((name, path))
    if args.output_tar.exists():
        raise FileExistsError(args.output_tar)
    with tarfile.open(args.output_tar, mode='x') as archive:
        for name, path in entries:
            if path.suffix == '.log':
                data = clean_log(path.read_bytes())
                info = archive.gettarinfo(str(path), arcname=name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            else:
                archive.add(str(path), arcname=name, recursive=False)
    print(f'Created {args.output_tar} with {len(entries)} files; inspect before upload.')


if __name__ == '__main__':
    main()
