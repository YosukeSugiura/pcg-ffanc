#!/usr/bin/env python3
"""Create a candidate archive from the manifest, sanitizing log copies.

Usage: python make_zenodo_archive.py SOURCE_ROOT OUTPUT_TAR [--section NAME] [--max-mib N]

ZENODO_MANIFEST.txt is divided into sections by lines '#@ section NAME'; entries before the first such line form
the section 'v1.0.0'. Without --section every entry is archived (the v1.0.0 behaviour). With --max-mib the entries
are split, in manifest order, into OUTPUT-part1.tar, OUTPUT-part2.tar, ... of at most N MiB each.
Review the archive before uploading it.
"""
import argparse
import io
from pathlib import Path
import re
import tarfile

BLOCK = 512
RECORD = 20 * BLOCK           # tarfile pads the archive to a multiple of the record size


def clean_log(data):
    text = data.decode('utf-8', errors='strict')
    text = re.sub(r'(?<![:/A-Za-z0-9_])/(?:home|workspace|usr|tmp|opt|root|mnt)/[^\s\x00"\x27<>|]*', '[absolute-path]', text)
    terms = ['G'+'PT', 'Clau'+'de', 'Co'+'dex', 'Op'+'us', 'Fa'+'ble',
             'Hai'+'ku', 'editor'+' advice', 'internal'+' note',
             'STRATEG'+'Y_', 'GAP_'+'THEOREM', 'PLAN_'+'TASLP', 'HAND'+'OFF']
    return re.sub('|'.join(map(re.escape, terms)), '[redacted]', text, flags=re.I).encode('utf-8')


def read_manifest():
    """[(section, name, size)] in manifest order."""
    entries, section = [], 'v1.0.0'
    for line in Path(__file__).with_name('ZENODO_MANIFEST.txt').read_text().splitlines():
        m = re.fullmatch(r'#@ section (\S+)', line.strip())
        if m:
            section = m.group(1)
            continue
        if not line or line.startswith('#'):
            continue
        name, size = line.split('\t')
        entries.append((section, name, int(size)))
    return entries


def member_bytes(size):
    """Upper bound of the bytes a regular file member occupies (header + padded data; long names use one extra
    header and data block, counted here for every member)."""
    return 3 * BLOCK + -(-size // BLOCK) * BLOCK


def write_tar(output, entries):
    if output.exists():
        raise FileExistsError(output)
    with tarfile.open(output, mode='x') as archive:
        for name, path in entries:
            if path.suffix == '.log':
                data = clean_log(path.read_bytes())
                info = archive.gettarinfo(str(path), arcname=name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            else:
                archive.add(str(path), arcname=name, recursive=False)
    print(f'Created {output} with {len(entries)} files ({output.stat().st_size} bytes); inspect before upload.')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source_root', type=Path)
    parser.add_argument('output_tar', type=Path)
    parser.add_argument('--section', help='archive only the entries of this manifest section (e.g. v1.2.0)')
    parser.add_argument('--max-mib', type=float, help='split into parts of at most this many MiB')
    args = parser.parse_args()
    source = args.source_root.resolve(strict=True)
    manifest = read_manifest()
    if args.section is not None:
        manifest = [e for e in manifest if e[0] == args.section]
        if not manifest:
            raise ValueError(f'No manifest entries in section {args.section}')
    entries = []
    for _, name, size in manifest:
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'Unsafe manifest path: {name}')
        path = (source / rel).resolve(strict=True)
        if not path.is_relative_to(source) or not path.is_file() or path.stat().st_size != size:
            raise ValueError(f'Missing, unsafe or size mismatch: {name}')
        entries.append((name, path, size))
    if args.max_mib is None:
        write_tar(args.output_tar, [(n, p) for n, p, _ in entries])
        return
    limit = int(args.max_mib * 2 ** 20) - 2 * RECORD          # end-of-archive blocks and final record padding
    parts, cur, used = [], [], 0
    for name, path, size in entries:
        need = member_bytes(size)
        if need > limit:
            raise ValueError(f'{name} alone exceeds {args.max_mib} MiB')
        if cur and used + need > limit:
            parts.append(cur)
            cur, used = [], 0
        cur.append((name, path))
        used += need
    parts.append(cur)
    out = args.output_tar
    stem = out.name[:-len('.tar')] if out.name.endswith('.tar') else out.name
    for i, part in enumerate(parts, 1):
        p = out.with_name(f'{stem}-part{i}.tar')
        write_tar(p, part)
        if p.stat().st_size > args.max_mib * 2 ** 20:
            raise RuntimeError(f'{p} exceeds {args.max_mib} MiB')


if __name__ == '__main__':
    main()
