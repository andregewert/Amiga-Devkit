# Amiga-Projekte – gemeinsame Hinweise für Claude

Gilt für alle Projekte, die `amiga-devkit` als Submodule einbinden (AmigaOS 3.2, Cross-Build
mit bebbos amiga-gcc unter `/opt/amiga`, NDK 3.2). Die `CLAUDE.md` des Projekts lädt diese
Datei mit `@amiga-devkit/docs/Amiga-Regeln.md` und legt fest, was davon abweicht.
Für Programme mit ReAction-Oberfläche gilt zusätzlich `amiga-devkit/docs/ReAction-Styleguide.md`.

## amiga-devkit

- Submodule im Projektverzeichnis `amiga-devkit/`, auf ein Tag gepinnt. Nicht im Submodule
  ändern; Änderungen gehören ins Repository `~/Dokumente/amiga-devkit`, dort committen und
  taggen, dann im Projekt `git -C amiga-devkit checkout <tag>` und `git add amiga-devkit`.
- `tools/amigaicons.py`: Workbench-Icons (klassisch, GlowIcons, NewIcons). Eingebaute Motive:
  `drawer`, `readme`, `license`, `install`, `tiles`. Eigene Motive meldet das Projekt mit
  `register(role, classic, glow, newicon)` an (`tools/mkicons.py` bzw. `tools/icons.py`).
- `tools/catcomp.py`: Kataloge (`.cd`/`.ct` → `strings.h` und `.catalog`).
- `tools/distlib.py`: Bausteine für `tools/mkdist.py` (Kopieren, README nach ISO-8859-1,
  Icons des Archivs mit `Icons/<Stil>/`-Sätzen, `lha`). `copy_devkit()` legt das Devkit in die
  Quellen des Archivs, denn die müssen ohne Git bauen.
- `make/charcheck.mk`: Ziel `charcheck` für die Dateien in `LATIN1`.
- `claude/settings.json`: Vorlage für den Hook, der nach jedem Write/Edit `make charcheck`
  ausführt; gehört als `.claude/settings.json` ins Projekt.

## Zeichenkodierung: ISO-8859-1

- Alles, was auf den Amiga geht oder von Amiga-Werkzeugen gelesen wird (Quellen, Header,
  Kataloge, Testdateien, `package/`, `LICENSE`, `Makefile`), ist **ISO-8859-1**. Niemals UTF-8
  in diese Dateien schreiben. Welche Verzeichnisse das sind, steht in `LATIN1` im `Makefile`.
- UTF-8 bleiben: `README*.md`, `CLAUDE.md`, `docs/*.md`, `tools/*.py`, `.claude/`.
- Neue Dateien dort ebenfalls in ISO-8859-1 anlegen. Wenn Umlaute nötig sind, die Datei mit
  Python schreiben (`open(p, 'w', encoding='latin-1')`) oder hinterher mit
  `iconv -f UTF-8 -t ISO-8859-1` umwandeln. In HTML-Dateien Entities (`&auml;` …) bevorzugen.
- Namen richtig schreiben, auch in C-Quellen: „André Gewert“ (é als 0xE9), nicht „Andre“.
  Sonst in C-Kommentaren möglichst ASCII.
- `make charcheck` (Teil von `make`) findet UTF-8-Sequenzen. Schlägt der Hook an, die genannte
  Datei sofort umwandeln.

## Bauen

- Bibliotheksbasen explizit mit `= NULL` initialisieren, sonst werden es COMMON-Symbole, die die
  Auto-Open-Stubs aus `libstubs.a` nachziehen.
- Programme setzen ihren Stack selbst (`__stack`, gelinkt mit `-Wl,-u,___stkinit`): Von der
  Workbench gibt ein Projekt-Icon oft nur 4 KB, zu wenig für ReAction, ASL und Datatypes.
  Große Puffer trotzdem nicht unnötig auf den Stack legen.
- Ohne Konsole gestartete Programme (Workbench) brauchen keine stdio-Funktionen (`sprintf` …):
  Sonst zieht libnix seine Konsolen-Initialisierung für den Workbench-Start nach.
- Code für 68020–68060 mit `-m68020-60 -mtune=68060` übersetzen: Ohne `-mtune=68060` erzeugt
  bebbos gcc 64-Bit-`mulu.l`/`divu.l` (z. B. für `x/255`), die der 68060 nur emuliert.
  In Pixel- und anderen heißen Schleifen keine `long long`-Arithmetik.

## Testen

- Logik, die ohne Amiga-Bibliotheken auskommt, als reines ANSI-C halten und mit Host-Tests
  (ASan/UBSan) in `make check` prüfen. Referenzausgaben (`.expected`) nach einer gewollten
  Änderung mit `make check-update` erneuern und den Diff prüfen, bevor sie eingecheckt werden.
- Vor einem Commit: `make` (enthält `charcheck`) und `make check`.
- GUI-Tests auf dem Amiga (Amiberry) macht der Benutzer selbst. Amiberry nicht mit seiner
  Konfiguration oder seinem Festplatten-Image starten. Ungetestete Annahmen über
  ReAction-Klassen im Commit/Bericht kennzeichnen.
- Fehlt ein Feature auf dem Amiga, das auf dem Host funktioniert, zuerst prüfen, welche Version
  geladen ist (`Version <datei> FULL`): Eine installierte oder residente alte Bibliothek/Klasse
  überdeckt den frischen Build. Alte Kopien entfernen bzw. mit `Avail FLUSH` aus dem Speicher
  werfen, erst dann im Code nach Fehlern suchen.

## Versionen und Aminet-Paket

- Versionsnummern (`$VER`, Version, Revision und Datum einer Bibliothek) werden nur zu einem
  offiziellen Release erhöht, bewusst und auf Ansage des Benutzers, nicht bei jeder Änderung
  oder jedem Build. Das Release bekommt eine neue Nummer, damit der Installer alte Versionen
  ersetzt. Zwischen zwei Releases bleibt die Nummer stehen; Entwicklungs-Builds lassen sich
  am Build-Verzeichnis bzw. am Datum der Datei unterscheiden, nicht an der Version.
- Datumsangaben (`$VER`, `$Id`, Bibliotheksdatum) immer `TT.MM.JJJJ`, Tag und Monat zweistellig
  mit führender Null, z. B. `01.10.2026`.
- `package/<Name>.readme` ist die Aminet-Readme: ISO-8859-1, Zeilen höchstens 78 Zeichen.
  Für Anwender sichtbare Änderungen knapp englisch (`History`) **und** deutsch
  (`Versionsgeschichte`) unter der kommenden Version eintragen; `Version:` wird mit dem
  Release angepasst. Kein `Replaces:`, solange Archivname und Aminet-Verzeichnis gleich
  bleiben.
- `make dist` baut `dist/<Name>.lha` mit `tools/mkdist.py`. Die Quellen im Archiv müssen ohne
  Git bauen (Submodule-Inhalte und Versionen mitkopieren).
- Neue Funktionen in `README.md` **und** `README.de.md` dokumentieren.

## Icons

- Die Dateien in `icons/` sind Beispiele zum Ansehen auf dem Amiga und werden mit
  `make icons` erzeugt, nie von Hand bearbeitet.
- NewIcons: Bildbreite 42 und 14 Farben sind Absicht (Paletten- und Zeilenenden fallen auf
  7-Bit-Grenzen), siehe Kommentare in `amigaicons.py`. Gezeichnet im Stil des NewIcons-Pakets
  (`Box`: isometrisch, Treppenkanten aus Pixelpaaren, Palette des Pakets, Werkzeuge und
  Schubladen auf einem Sockel), eigene Motive, keine Pixel aus dem Paket. Ausgewählt zeigen
  NewIcons ein leicht geändertes Bild, kein abgedunkeltes: jedes NewIcons-Motiv zeichnet beide
  Zustände (`sel`).
