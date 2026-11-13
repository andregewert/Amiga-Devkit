#!/usr/bin/env python3
# doxy2guide.py - AmigaGuide reference from Doxygen's XML output (amiga-devkit)
#
# Copyright (c) 2026 André Gewert <agewert@ubergeek.de>, MIT License
#
# Amiga browsers cannot show Doxygen's HTML (CSS, JavaScript, UTF-8). This
# turns the XML output of the same comments (GENERATE_XML) into one
# AmigaGuide file in ISO-8859-1, laid out like the classic Autodocs:
#
#   MAIN        overview: the documented files and their groups (@name)
#   <file>      the @file text of a header and links to its groups
#   <group>     one node per @name group (or kind of member): a list of its
#               members; members with only a short comment (/**< ... */)
#               are described right there
#   <member>    one node per function and per member with a longer comment:
#               NAME, SYNOPSIS, FUNCTION, INPUTS, RESULT, NOTES, SEE ALSO
#   Index       all names, alphabetically
#
# References (#PIXOOA_Size, PixooPush()) become links. Lines are wrapped at
# 76 columns, code examples are kept as they are. make/docs.mk calls this
# with DOXYGEN_GUIDE.
#
# Usage: doxy2guide.py XMLDIR OUTPUT.guide --name NAME [--version V]

import argparse, os, re, sys
import xml.etree.ElementTree as ET

WIDTH = 76
INDENT = 4

# characters that ISO-8859-1 lacks
LATIN1_TABLE = {'„': '"', '“': '"', '”': '"', '‘': "'", '’': "'",
                '–': '-', '—': '-', '…': '...', '→': '->', '←': '<-',
                '≤': '<=', '≥': '>=', ' ': ' ', '•': '*', '×': 'x'}


def latin1(s):
    out = []
    for ch in s:
        ch = LATIN1_TABLE.get(ch, ch)
        try:
            ch.encode('latin-1')
        except UnicodeEncodeError:
            ch = '?'
        out.append(ch)
    return ''.join(out)


def esc(s):
    """ text for AmigaGuide: backslash and @ are special """
    return latin1(s).replace('\\', '\\\\').replace('@', '\\@')


# ------------------------------------------------------------- inline text ---
# A run of inline text is a list of tokens (visible, raw): visible counts for
# the line width, raw is written (with links and escapes). Spaces are tokens
# of their own; a link is one token that is never split.

class Ctx:
    """ maps refids to nodes while rendering """
    def __init__(self, target):
        self.target = target        # refid -> node name

    def link(self, refid, label):
        node = self.target.get(refid)
        label = latin1(label)
        if not node or '"' in label:
            return (label, esc(label))
        return (label, '@{"%s" link "%s"}' % (label.replace('\\', '\\\\'), node))


def words(text):
    toks = []
    for part in re.split(r'(\s+)', text):
        if not part:
            continue
        if part.isspace():
            toks.append((' ', ' '))
        else:
            toks.append((latin1(part), esc(part)))
    return toks


def inline(e, ctx, toks):
    """ tokens of an element's inline content (blocks are skipped) """
    if e.text:
        toks += words(e.text)
    for c in e:
        if c.tag in BLOCK_TAGS:
            pass
        elif c.tag == 'ref':
            toks.append(ctx.link(c.get('refid'), ''.join(c.itertext())))
        elif c.tag in ('bold', 'emphasis'):
            sub = []
            inline(c, ctx, sub)
            on, off = ('@{b}', '@{ub}') if c.tag == 'bold' else ('@{i}', '@{ui}')
            if sub:
                sub[0] = (sub[0][0], on + sub[0][1])
                sub[-1] = (sub[-1][0], sub[-1][1] + off)
            toks += sub
        elif c.tag == 'linebreak':
            toks.append(('\n', '\n'))
        elif c.tag == 'sp':
            toks.append((' ', ' '))
        elif c.tag == 'ulink':
            text = ''.join(c.itertext())
            url = c.get('url', '')
            same = text in (url, re.sub(r'^mailto:', '', url))
            toks += words(text if same else '%s (%s)' % (text, url))
        else:                       # computeroutput, anchor, ... : just the text
            inline(c, ctx, toks)
        if c.tail:
            toks += words(c.tail)
    return toks


def wrap(toks, indent, first=None, width=WIDTH):
    """ wrapped lines; first: prefix of the first line (same visible width
        as indent), e.g. a parameter name                                  """
    lines, line, col = [], first if first is not None else ' ' * indent, indent
    have = False
    pending = False
    for vis, raw in toks:
        if vis == '\n':
            lines.append(line.rstrip())
            line, col, have, pending = ' ' * indent, indent, False, False
            continue
        if vis == ' ':
            pending = have
            continue
        need = len(vis) + (1 if pending else 0)
        if have and col + need > width:
            lines.append(line.rstrip())
            line, col, pending = ' ' * indent, indent, False
            need = len(vis)
        if pending:
            line += ' '
            col += 1
        line += raw
        col += len(vis)
        have, pending = True, False
    if have or first is not None:
        lines.append(line.rstrip())
    return lines


def plain(toks):
    """ the visible text of tokens on one line """
    return re.sub(r'\s+', ' ', ''.join(v for v, _ in toks)).strip()


# ------------------------------------------------------------------ blocks ---
# Descriptions become blocks: ('para', toks), ('code', [raw lines]),
# ('list', [blocks of each item]), ('params', [(name, blocks)]),
# ('sect', kind, blocks) for @return, @note, @see ...

BLOCK_TAGS = {'parameterlist', 'simplesect', 'programlisting', 'verbatim', 'itemizedlist',
              'orderedlist', 'table', 'heading', 'preformatted', 'xrefsect'}


def blocks(e, ctx):
    """ the blocks of a description element (briefdescription, para ...) """
    out = []
    if e is None:
        return out
    for p in e:
        if p.tag == 'para':
            out += para_blocks(p, ctx)
        elif p.tag in BLOCK_TAGS:
            out += block(p, ctx)
    return out


def para_blocks(p, ctx):
    """ a <para>: inline runs interrupted by nested blocks """
    out, toks = [], []
    if p.text:
        toks += words(p.text)
    for c in p:
        if c.tag in BLOCK_TAGS:
            if plain(toks):
                out.append(('para', toks))
            toks = []
            out += block(c, ctx)
        else:
            holder = ET.Element('x')
            holder.append(c)
            inline(holder, ctx, toks)
            continue                # tail handled by inline()
        if c.tail:
            toks += words(c.tail)
    if plain(toks) and not plain(toks).startswith('$VER:'):
        out.append(('para', toks))      # (a second $VER would confuse Version)
    return out


def block(c, ctx):
    if c.tag == 'parameterlist':
        items = []
        for item in c.findall('parameteritem'):
            names = ', '.join(''.join(n.itertext()) for n in item.iter('parametername'))
            d = item.find('parameternamelist/parametername')
            direction = d.get('direction') if d is not None else None
            if direction in ('out', 'inout'):
                names += ' (%s)' % direction.replace('inout', 'in/out')
            items.append((latin1(names), blocks(item.find('parameterdescription'), ctx)))
        return [('params', c.get('kind'), items)]
    if c.tag == 'simplesect':
        return [('sect', c.get('kind'), blocks(c, ctx))]
    if c.tag == 'xrefsect':
        title = ''.join(c.find('xreftitle').itertext()) if c.find('xreftitle') is not None else ''
        return [('sect', title.lower() or 'note', blocks(c.find('xrefdescription'), ctx))]
    if c.tag == 'programlisting':
        lines = []
        for cl in c.findall('codeline'):
            toks = inline(cl, ctx, [])
            lines.append(''.join(raw for _, raw in toks).rstrip())
        while lines and not lines[-1]:
            lines.pop()
        return [('code', lines)]
    if c.tag in ('verbatim', 'preformatted'):
        return [('code', [esc(l) for l in ''.join(c.itertext()).rstrip('\n').split('\n')])]
    if c.tag in ('itemizedlist', 'orderedlist'):
        return [('list', c.tag == 'orderedlist', [blocks(li, ctx) for li in c.findall('listitem')])]
    if c.tag == 'heading':
        return [('para', [(v.upper(), r.upper()) for v, r in inline(c, ctx, [])])]
    if c.tag == 'table':
        out = []
        for row in c.findall('row'):
            cells = [plain(inline_all(entry, ctx)) for entry in row.findall('entry')]
            out.append(('para', words(' | '.join(cells))))
        return out
    return []


def inline_all(e, ctx):
    """ all text of an element as tokens, paragraphs joined """
    toks = []
    for p in e.iter('para'):
        inline(p, ctx, toks)
        toks.append((' ', ' '))
    return toks


def render(bl, indent):
    """ lines of blocks, paragraphs separated by empty lines """
    out = []
    for b in bl:
        if out and out[-1] != '':
            out.append('')
        if b[0] == 'para':
            out += wrap(b[1], indent)
        elif b[0] == 'code':
            out += [' ' * (indent + 2) + l if l else '' for l in b[1]]
        elif b[0] == 'list':
            for n, item in enumerate(b[2]):
                mark = '%d. ' % (n + 1) if b[1] else '- '
                lines = render(item, indent + len(mark))
                if lines:
                    lines[0] = ' ' * indent + mark + lines[0][indent + len(mark):]
                out += lines
        elif b[0] == 'params':
            out += render_params(b[2], indent)
        elif b[0] == 'sect':
            label = b[1].capitalize() + ': '
            lines = render(b[2], indent)
            if lines:
                lines[0] = ' ' * indent + label + lines[0][indent:]
            out += lines
    while out and out[-1] == '':
        out.pop()
    return out


def render_params(items, indent):
    out = []
    for name, bl in items:
        head = name + ' - '
        if len(head) > 16:              # long names: description below
            out.append(' ' * indent + esc(name))
            out += render(bl, indent + 4)
            continue
        lines = []
        for b in bl:
            if b[0] == 'para' and not lines:
                lines += wrap(b[1], indent + len(head), ' ' * indent + esc(head))
            else:
                if lines:
                    lines.append('')
                lines += render([b], indent + len(head))
        out += lines or [' ' * indent + esc(name)]
    return out


# ----------------------------------------------------------------- members ---

def text_of(e):
    return latin1(''.join(e.itertext())) if e is not None else ''


class Member:
    def __init__(self, e, ctx):
        self.e = e
        self.id = e.get('id')
        self.kind = e.get('kind')
        self.name = text_of(e.find('name'))
        self.node = None            # own node, or None
        self.parse(ctx)

    def parse(self, ctx):
        """ (re)build the description blocks: links need all nodes, so
            this runs again once every node has its name               """
        self.brief = blocks(self.e.find('briefdescription'), ctx)
        self.detail = blocks(self.e.find('detaileddescription'), ctx)

    def summary(self):
        """ tokens of a one-paragraph summary """
        if self.brief:
            return self.brief[0][1] if self.brief[0][0] == 'para' else []
        if self.detail and self.detail[0][0] == 'para':
            return self.detail[0][1]
        return []

    def rest(self):
        """ the detailed blocks that the summary does not cover """
        if not self.brief and self.detail and self.detail[0][0] == 'para':
            return self.detail[1:]
        return self.detail

    def needs_node(self):
        return self.kind in ('function', 'enum') or bool(self.rest())

    def synopsis(self):
        e = self.e
        if self.kind == 'function':
            head = '%s%s(' % (spaced(text_of(e.find('type'))), self.name)
            args = [decl(text_of(p.find('type')), text_of(p.find('declname')))
                    for p in e.findall('param')]
            return fit_call(head, args or ['void'], ');')
        if self.kind == 'define':
            params = [text_of(p.find('defname')) for p in e.findall('param')]
            s = '#define ' + self.name + ('(%s)' % ', '.join(params) if e.find('param') is not None else '')
            init = text_of(e.find('initializer'))
            return [s + (' ' + init if init else '')]
        if self.kind == 'typedef':
            return [plain(words(text_of(e.find('definition')) + text_of(e.find('argsstring')))) + ';']
        if self.kind == 'variable':
            return [plain(words(text_of(e.find('definition')))) + ';']
        if self.kind == 'enum':
            lines = ['enum %s {' % self.name if not self.name.startswith('@') else 'enum {']
            for v in e.findall('enumvalue'):
                init = text_of(v.find('initializer'))
                lines.append('    %s%s,' % (text_of(v.find('name')), ' ' + init if init else ''))
            return lines + ['};']
        return [self.name]


def decl(t, n):
    """ "struct TagItem *" and "tags" -> "struct TagItem *tags" """
    t = plain(words(t))
    return (t + ('' if t.endswith('*') or not n else ' ') + n).strip()


def spaced(t):
    t = plain(words(t))
    return t + ('' if t.endswith('*') else ' ')


def fit_call(head, args, tail):
    one = head + ', '.join(args) + tail
    if len(one) <= WIDTH - INDENT:
        return [one]
    lines, line = [], head
    pad = ' ' * len(head)
    for i, a in enumerate(args):
        piece = a + (tail if i == len(args) - 1 else ',')
        if line.strip() and line != head and len(line) + 1 + len(piece) > WIDTH - INDENT:
            lines.append(line.rstrip())
            line = pad
        line += ('' if line in (head, pad) else ' ') + piece
    lines.append(line)
    return lines


# ---------------------------------------------------------------- the guide ---

SECTION_TITLES = {'func': 'Functions', 'define': 'Macros', 'typedef': 'Types', 'enum': 'Enumerations',
                  'var': 'Variables', 'user-defined': ''}


class Group:
    def __init__(self, title, desc, members):
        self.title, self.desc, self.members = title, desc, members
        self.node = None


def node_name(s, used):
    base = re.sub(r'[^A-Za-z0-9_.]+', '_', s).strip('_') or 'node'
    n, i = base, 2
    while n.lower() in used:
        n = '%s_%d' % (base, i)
        i += 1
    used.add(n.lower())
    return n


def build(xmldir, name, version):
    index = ET.parse(os.path.join(xmldir, 'index.xml')).getroot()
    target = {}
    ctx = Ctx(target)
    used = {'main', 'index'}
    files, structs = [], {}
    for comp in index.findall('compound'):
        kind = comp.get('kind')
        if kind not in ('file', 'struct', 'union'):
            continue
        cd = ET.parse(os.path.join(xmldir, comp.get('refid') + '.xml')).getroot().find('compounddef')
        if kind == 'file':
            files.append(cd)
        else:
            structs[cd.get('id')] = cd

    # nodes first (links need them), text afterwards
    model = []
    for cd in files:
        loc = cd.find('location')
        path = loc.get('file') if loc is not None else text_of(cd.find('compoundname'))
        path = re.sub(r'^include/', '', path)
        fnode = node_name(path, used)
        target[cd.get('id')] = fnode
        groups = []
        for sd in cd.findall('sectiondef'):
            title = re.sub(r'#(?=\w)', '', text_of(sd.find('header'))) or SECTION_TITLES.get(sd.get('kind'), sd.get('kind'))
            members = [Member(m, ctx) for m in sd.findall('memberdef')]
            g = Group(title, sd.find('description'), members)
            g.node = node_name(path + '_' + title, used)
            for m in members:
                if m.needs_node():
                    m.node = node_name(m.name, used)
                target[m.id] = m.node or g.node
                for v in m.e.findall('enumvalue'):
                    target[v.get('id')] = m.node or g.node
            groups.append(g)
        snodes = []
        for ic in cd.findall('innerclass'):
            s = structs.get(ic.get('refid'))
            if s is not None:
                n = node_name(text_of(s.find('compoundname')), used)
                target[s.get('id')] = n
                for m in s.iter('memberdef'):
                    target[m.get('id')] = n
                snodes.append((s, n))
        model.append((cd, path, fnode, groups, snodes))
    for _, _, _, groups, _ in model:
        for g in groups:
            for m in g.members:
                m.parse(ctx)

    out = ['@DATABASE "%s.guide"' % name,
           '@$VER: %s.guide %s' % (name, version) if version else '',
           '@REMARK generated by amiga-devkit/tools/doxy2guide.py from the Doxygen comments',
           '@INDEX "Index"',
           '@WIDTH %d' % WIDTH]
    out = [l for l in out if l]
    index_entries = []

    # MAIN
    title = '%s %s' % (name, version) if version else name
    lines = ['', '@{b}%s@{ub}' % esc(title), '']
    for cd, path, fnode, groups, snodes in model:
        brief = plain(blocks(cd.find('briefdescription'), ctx)[0][1]) if blocks(cd.find('briefdescription'), ctx) else ''
        lines.append('  @{"%s" link "%s"}' % (esc(path), fnode))
        if brief:
            lines += wrap(words(brief), 6)
        for g in groups:
            lines.append('      @{"%s" link "%s"}' % (esc(g.title), g.node))
        for s, n in snodes:
            lines.append('      @{"%s" link "%s"}' % (esc(text_of(s.find('compoundname'))), n))
        lines.append('')
    lines.append('  @{"Index" link "Index"}')
    out += node('MAIN', title, lines)

    for cd, path, fnode, groups, snodes in model:
        # file node: the @file text
        lines = ['', '@{b}%s@{ub}' % esc(path), '']
        bl = blocks(cd.find('briefdescription'), ctx) + blocks(cd.find('detaileddescription'), ctx)
        lines += render(bl, 2)
        lines += ['', '@{b}Contents@{ub}', '']
        for g in groups:
            lines.append('  @{"%s" link "%s"}' % (esc(g.title), g.node))
        for s, n in snodes:
            lines.append('  @{"%s" link "%s"}' % (esc(text_of(s.find('compoundname'))), n))
        out += node(fnode, path, lines, toc='MAIN')
        index_entries.append((path, fnode))

        for g in groups:
            lines = ['', '@{b}%s@{ub}' % esc(g.title), '']
            d = blocks(g.desc, ctx)
            if d:
                lines += render(d, 2) + ['']
            for m in g.members:
                index_entries.append((m.name, m.node or g.node))
                summary = m.summary()
                if m.node:
                    lines.append('  @{"%s" link "%s"}' % (esc(m.name), m.node))
                    if summary:
                        lines += wrap(summary, 6)
                else:
                    syn = m.synopsis()
                    lines += ['  ' + esc(syn[0])] + ['  ' + esc(l) for l in syn[1:]]
                    if summary:
                        lines += wrap(summary, 6)
                    for v in m.e.findall('enumvalue'):
                        vs = blocks(v.find('briefdescription'), ctx) + blocks(v.find('detaileddescription'), ctx)
                        vt = vs[0][1] if vs and vs[0][0] == 'para' else []
                        lines += wrap(vt, 10, '      ' + esc(text_of(v.find('name'))).ljust(4) + ' ') if vt \
                            else ['      ' + esc(text_of(v.find('name')))]
                lines.append('')
            out += node(g.node, '%s: %s' % (path, g.title), lines, toc=fnode)
            for m in g.members:
                if m.node:
                    out += member_node(m, ctx, g.node)

        for s, n in snodes:
            out += struct_node(s, n, ctx, fnode)
            index_entries.append((text_of(s.find('compoundname')), n))

    # Index
    lines = ['', '@{b}Index@{ub}', '']
    seen = set()
    for label, n in sorted(index_entries, key=lambda x: x[0].lower()):
        if (label, n) in seen:
            continue
        seen.add((label, n))
        lines.append('  @{"%s" link "%s"}' % (esc(label), n))
    out += node('Index', 'Index', lines)
    return '\n'.join(out) + '\n'


def node(name, title, lines, toc=None):
    head = ['', '@NODE "%s" "%s"' % (name, esc(title))]
    if toc:
        head.append('@TOC "%s"' % toc)
    return head + lines + ['@ENDNODE']


def section(title, lines):
    return ['@{b}%s@{ub}' % title] + lines + [''] if lines else []


def member_node(m, ctx, toc):
    syn = ['    ' + esc(l) for l in m.synopsis()]
    rest = m.rest()
    main = [b for b in rest if b[0] not in ('params', 'sect')]
    params = [it for b in rest if b[0] == 'params' for it in b[2]]
    sects = {}
    for b in rest:
        if b[0] == 'sect':
            sects.setdefault(b[1], []).extend(b[2])
    summary = plain(m.summary())
    lines = ['']
    lines += section('NAME', wrap(words('%s -- %s' % (m.name, summary) if summary else m.name), INDENT + 4,
                                  ' ' * INDENT) if summary else ['    ' + esc(m.name)])
    lines += section('SYNOPSIS', syn)
    label = 'FUNCTION' if m.kind == 'function' else 'DESCRIPTION'
    lines += section(label, render(main, INDENT))
    lines += section('INPUTS', render_params(params, INDENT))
    lines += section('RESULT', render(sects.pop('return', []) + sects.pop('retval', []), INDENT))
    for kind in ('note', 'warning', 'attention', 'pre', 'post', 'since', 'deprecated'):
        if kind in sects:
            lines += section(kind.upper() + ('S' if kind == 'note' else ''), render(sects.pop(kind), INDENT))
    see = sects.pop('see', [])
    for kind in sorted(sects):
        lines += section(kind.upper(), render(sects[kind], INDENT))
    lines += section('SEE ALSO', render(see, INDENT))
    while lines and lines[-1] == '':
        lines.pop()
    return node(m.node, m.name, lines, toc=toc)


def struct_node(s, n, ctx, toc):
    name = text_of(s.find('compoundname'))
    kind = s.get('kind')
    members = [Member(m, ctx) for m in s.iter('memberdef')]
    syn = ['    %s %s {' % (kind, esc(name))]
    width = max([len(plain(words(text_of(m.e.find('type')) + ' ' + m.name + text_of(m.e.find('argsstring')))))
                 for m in members] + [0]) + 1
    for m in members:
        decl = plain(words(text_of(m.e.find('type')) + ' ' + m.name + text_of(m.e.find('argsstring')))) + ';'
        summary = m.summary()
        if summary:
            syn += wrap(summary, INDENT + 4 + width + 1, ' ' * (INDENT + 4) + esc(decl).ljust(width + 1))
        else:
            syn.append(' ' * (INDENT + 4) + esc(decl))
    syn.append('    };')
    bl = blocks(s.find('briefdescription'), ctx)
    summary = plain(bl[0][1]) if bl and bl[0][0] == 'para' else ''
    lines = ['']
    lines += section('NAME', wrap(words('%s %s -- %s' % (kind, name, summary)), INDENT + 4, ' ' * INDENT))
    lines += section('SYNOPSIS', syn)
    lines += section('DESCRIPTION', render(bl[1:] + blocks(s.find('detaileddescription'), ctx), INDENT))
    while lines and lines[-1] == '':
        lines.pop()
    return node(n, '%s %s' % (kind, name), lines, toc=toc)


def main():
    ap = argparse.ArgumentParser(description='AmigaGuide reference from Doxygen XML')
    ap.add_argument('xmldir')
    ap.add_argument('output')
    ap.add_argument('--name', required=True, help='name of the documented library or program')
    ap.add_argument('--version', default='')
    a = ap.parse_args()
    text = build(a.xmldir, a.name, a.version)
    with open(a.output, 'w', encoding='latin-1', newline='\n') as f:
        f.write(text)


if __name__ == '__main__':
    main()
