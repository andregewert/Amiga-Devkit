#!/usr/bin/env python3
# distlib.py - helpers for building Aminet archives (amiga-devkit)
#
# Copyright (c) 2026 André Gewert <agewert@ubergeek.de>, MIT License
#
# The mkdist.py of a project collects its files in dist/<NAME>/ with
# copy()/copytree(), gives them icons with package_icons() and packs the
# archive with pack(). Icons come from amigaicons.py; the project registers
# its own motifs there before it calls package_icons().

import os, shutil, subprocess

from amigaicons import STYLES, WBDRAWER, WBPROJECT, write_icon

DEVKIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copytree(src, dst, ignore=()):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*ignore), dirs_exist_ok=True)


def copy_devkit(dst):
    """ the devkit itself, for source archives that must build without git """
    copytree(DEVKIT, dst, ignore=('.git', '__pycache__'))


def to_latin1_text(md):
    """ UTF-8 text (README*.md) as ISO-8859-1 bytes for the Amiga """
    table = {'„': '"', '“': '"', '”': '"', '–': '-', '—': '-',
             '…': '...', '→': '->', '≤': '<=', '≥': '>=', '’': "'"}
    return ''.join(table.get(ch, ch) for ch in md).encode('latin-1', 'replace')


def latin1_copy(src, dst):
    with open(src, encoding='utf-8') as f:
        text = to_latin1_text(f.read())
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'wb') as f:
        f.write(text)


def package_icons(pkg, name, icons, drawer_icon=None):
    """ classic icons next to the files, every style also in Icons/<Style>/
        together with a script Icons/Use<Style> that copies that set over.
        icons: (path in pkg, role, kind, write_icon keywords).
        drawer_icon: name of the package drawer's icon in Icons/<Style>/,
        needed if a file in pkg is called like the package (Kickdown).  """
    drawer_icon = drawer_icon or name
    write_icon(pkg, 'Classic', 'drawer', WBDRAWER)
    for path, role, kind, kw in icons:
        write_icon(os.path.join(pkg, path), 'Classic', role, kind, **kw)
    for style in STYLES:
        sets = os.path.join(pkg, 'Icons', style)
        write_icon(os.path.join(sets, drawer_icon), style, 'drawer', WBDRAWER)
        for path, role, kind, kw in icons:
            write_icon(os.path.join(sets, path), style, role, kind, **kw)
        target = '' if drawer_icon == name else name + '.info'
        script = os.path.join(pkg, 'Icons', 'Use' + style)
        with open(script, 'w', encoding='latin-1', newline='\n') as f:
            f.write('; gives the files of %s the %s icons\n'
                    '; (double click, IconX runs it in this drawer)\n'
                    'Copy %s/~(%s.info) / ALL CLONE QUIET\n'
                    'Copy %s/%s.info //%s CLONE QUIET\n'
                    'Echo "%s icons copied. Close and reopen the drawers to see them."\n'
                    % (name, style, style, drawer_icon, style, drawer_icon, target, style))
        write_icon(script, style, 'tiles', WBPROJECT, default_tool='C:IconX')


def pack(dist, name):
    """ dist/<name>.lha from dist/<name>/ and its icon, plus dist/<name>.readme
        (the Aminet readme, expected as dist/<name>/<name>.readme)        """
    pkg = os.path.join(dist, name)
    arc = os.path.join(dist, name + '.lha')
    files = [name + '.info']
    for dirpath, dirnames, filenames in os.walk(pkg):
        dirnames.sort()
        for fn in sorted(filenames):
            files.append(os.path.relpath(os.path.join(dirpath, fn), dist))
    # an LhA that can create archives: jlha (Debian: jlha-utils) or lha for UNIX
    tool = shutil.which('jlha') or 'lha'
    subprocess.run([tool, 'ao5q', arc] + files, cwd=dist, check=True)
    shutil.copy2(os.path.join(pkg, name + '.readme'), os.path.join(dist, name + '.readme'))
    print('created', arc, os.path.getsize(arc), 'bytes')
