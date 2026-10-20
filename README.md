# amiga-devkit

Shared tools and guidelines for AmigaOS 3.2 projects cross-compiled with bebbo's amiga-gcc,
used as a git submodule by
[html.gadget](https://github.com/andregewert/Amiga-HTML-Gadget) and
[Kickdown](https://github.com/andregewert/Amiga-Kickdown).

| Path | Contents |
|---|---|
| `tools/amigaicons.py` | Workbench icons drawn in code: classic 4 colour, GlowIcons and NewIcons. Built-in motifs: `drawer`, `readme`, `license`, `install`, `tiles`; projects add their own with `register()`. |
| `tools/catcomp.py` | locale.library catalogs: `.cd`/`.ct` (CatComp/FlexCat format) to `strings.h` and `.catalog` in the format of the OS 3.2 catalogs. |
| `tools/distlib.py` | Building blocks for an Aminet archive: copying, README to ISO-8859-1, icons for every file plus complete `Icons/<Style>/` sets, packing with lha. |
| `make/charcheck.mk` | `make charcheck`: refuses UTF-8 in files that must be ISO-8859-1. |
| `make/docs.mk`, `doxygen/Doxyfile.base` | HTML documentation from the code's Javadoc-style comments with Doxygen; the targets fail on any documentation warning. |
| `claude/settings.json` | Claude Code hook running `make charcheck` after every edit (copy to `.claude/`). |
| `docs/Amiga-Regeln.md` | Shared notes for AI assistants (German), imported by the projects' `CLAUDE.md`. |
| `docs/ReAction-Styleguide.md` | Style guide for ReAction applications (German). |
| `docs/Dokumentation.md` | Rules for documentation comments (Doxygen, Javadoc style) instead of hand-written Autodocs (German). |

Python 3 only, no other dependencies (Doxygen for the documentation targets).

## Using it in a project

```sh
git submodule add https://github.com/andregewert/Amiga-Devkit.git amiga-devkit
git -C amiga-devkit checkout v1.0
mkdir -p .claude && cp amiga-devkit/claude/settings.json .claude/
```

Makefile:

```make
DEVKIT  := amiga-devkit
ifeq ($(wildcard $(DEVKIT)/make/charcheck.mk),)
$(error $(DEVKIT) is missing: git submodule update --init)
endif
LATIN1  := $(wildcard src/*.c src/*.h package/* LICENSE Makefile)
include $(DEVKIT)/make/charcheck.mk

all: charcheck ...
```

Python (`tools/mkicons.py`, `tools/mkdist.py`):

```python
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'amiga-devkit', 'tools'))
import amigaicons as ai

ai.register('myapp', pic_myapp, m_myapp, n_myapp)
ai.write_samples(os.path.join(ROOT, 'icons'), SAMPLES)
```

`CLAUDE.md`:

```markdown
@amiga-devkit/docs/Amiga-Regeln.md
```

## License

MIT, see `LICENSE`.
