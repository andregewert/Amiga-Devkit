# Dokumentationskommentare – gemeinsame Regeln

Gilt für alle Projekte mit `amiga-devkit`. Die `CLAUDE.md` des Projekts lädt diese Datei mit
`@amiga-devkit/docs/Dokumentation.md`.

## Wohin welches Wissen gehört

Die README ist für Menschen, das technische Wissen steht dort, wo es beim Arbeiten am Code
gelesen wird:

| Ort | Für wen | Inhalt |
|---|---|---|
| `README.md`, `README.de.md` | Anwender, neugierige Entwickler | was das Programm kann (Stichpunkte), Voraussetzungen als knappe Liste ohne Begründungen, Start, Optionen und Tooltypes (Tabelle), Bauen in wenigen Zeilen, Credits und Lizenz |
| Code-Kommentare (Doxygen) | wer das Modul ändert | was nur ein Modul betrifft: sein Verhalten, Rückfallwege, Fallen der OS-Klassen, die es benutzt (im `@file`-Kopf oder an der Funktion) |
| `TECHNICAL.md` | die KI und Entwickler | was mehrere Module übergreift: Zusammenspiel, Abläufe, Erkenntnisse über OS-Klassen, die mehrere Stellen betreffen; nach Themen gegliedert |
| `AGENTS.md` / `CLAUDE.md` | die KI (wird jede Sitzung geladen) | Aufbau, Konventionen, verbindliche Regeln, Verweise auf die Abschnitte von `TECHNICAL.md` („vor Änderungen an X lesen“) |

- **Die README bleibt kurz.** Technische Einzelheiten (wann etwas neu gezeichnet wird, welche
  Klassenversion was kann, Abläufe im Code) gehören nicht hinein. Neue Funktionen bekommen dort
  einen Stichpunkt, Optionen und Tooltypes einen Tabelleneintrag.
- **Erst in den Code, dann in `TECHNICAL.md`:** Was sich einem Modul zuordnen lässt, steht in
  dessen Kommentar, denn der wird beim Ändern sicher mitgelesen. `TECHNICAL.md` hält nur, was
  dort keinen Platz hat.
- **`TECHNICAL.md` wird nicht mit `@` geladen**, damit nicht jede Sitzung den ganzen Text
  mitschleppt. `AGENTS.md` (oder `CLAUDE.md`) verweist auf die Abschnitte, die vor bestimmten
  Änderungen zu lesen sind.
- **Sprache:** README englisch und deutsch, `TECHNICAL.md` und `AGENTS.md` englisch (UTF-8).

## Grundsätze

- **Eine Quelle:** Die Dokumentation steht als Kommentar im Code, im Javadoc-Stil, den Doxygen
  versteht. Daraus entsteht HTML (`make docs`). Klassische Autodocs (`.doc`) werden nicht mehr
  von Hand geschrieben. Wird für ein Aminet-Paket später eine `.doc`-Datei gebraucht, wird sie aus
  denselben Kommentaren erzeugt.
- **Alles wird dokumentiert:**
  - jede Datei mit `@file` (ohne diesen Kopf übergeht Doxygen ihre Funktionen),
  - jede Funktion, auch `static`,
  - jeder Typ (`struct`, `union`, `enum`, `typedef`) mit seinen Feldern und Werten,
  - jedes Makro und jede globale Variable, die eine Schnittstelle sind.
- **Öffentliche Schnittstellen** von Klassen und Bibliotheken werden im öffentlichen Header
  dokumentiert (`include/gadgets/<name>.h`), nicht in der `.c`-Datei. Wer die Klasse benutzt,
  braucht nur den Header: Er ist zugleich die Referenz.
- **Die Kommentare erklären das Was und das Warum:**
  - was eine Funktion tut, was sie voraussetzt und was sie zurückgibt,
  - wem Speicher gehört und wer ihn freigibt,
  - in welchem Kontext sie laufen darf (Prozess, `input.device`, Hook),
  - welche Fallen es gibt, z. B. Verhalten einer OS-Klasse, das im Maschinencode nachgesehen
    wurde.
- **Englisch und knapp, möglichst ASCII**, wie die übrigen Kommentare. Namen wie „André Gewert“
  bleiben richtig geschrieben (ISO-8859-1).
- **Prüfung:** `make docs` ruft Doxygen auf und schlägt fehl, sobald es warnt (fehlender
  Kommentar, Parameter ohne `@param`, `@param` mit falschem Namen). Vor einem Commit, der
  Schnittstellen ändert, läuft `make docs` ohne Warnung. Doxygen wird nur dafür gebraucht, nie
  für den eigentlichen Build.

## Form

- **Kommentarblock:** `/** ... */` direkt vor der Deklaration.
  - Die erste Zeile ist `@brief` mit einem Satz.
  - Danach, wenn nötig, eine Leerzeile und längere Erklärungen.
  - Dann `@param` für jeden Parameter und `@return`, außer bei `void`.
  - Weitere Befehle: `@note`, `@warning`, `@see`, `@code`/`@endcode`.
- **Kurzform:** Felder, Aufzählungswerte und einfache Makros dürfen eine nachgestellte
  Kurzform `/**< ... */` haben.
- **Deklaration und Definition:** Eine Funktion, die in einem Header deklariert ist, wird dort
  dokumentiert. Die Definition in der `.c`-Datei braucht dann keinen zweiten Block. Ein kurzer
  normaler Kommentar mit Hinweisen zur Umsetzung ist dort erlaubt.
- **Stil der Befehle:** `@`, nicht `\`. Keine Typen in `@param` wiederholen. `@param[out]` und
  `@param[in,out]` kennzeichnen Ausgabeparameter.

```c
/**
 * @file search.c
 * @brief Portable search engine of the find window (plain text and POSIX
 *        regular expressions, line by line).
 */

/** A match within one line (columns, end exclusive). */
typedef struct SearchMatch {
    long start;     /**< first column */
    long end;       /**< column after the match */
} SearchMatch;

/**
 * @brief Find the first match in a line that starts at or after a column.
 *
 * Runs regexec() with REG_STARTEND, so the line needs no terminator.
 *
 * @param p The compiled pattern.
 * @param line The line (need not be terminated).
 * @param length Its length.
 * @param from The first column a match may start at.
 * @param[out] m The match, if one is found.
 * @return Non-zero if a match was found.
 */
int search_line_next(const SearchPattern *p, const char *line, long length, long from,
                     SearchMatch *m);
```

## Klassen und Bibliotheken (öffentlicher Header)

Der Header ersetzt die Autodocs. Die Gliederung entspricht ihren gewohnten Abschnitten:

- **Dateikopf** (`@file`): wozu die Klasse dient, Superklasse, Klassenname, Pfad der Bibliothek,
  ein Anwendungsbeispiel in `@code` und Hinweise zum Kontext, z. B. „nur vom Prozess der
  Anwendung, nicht aus einer Notification“.
- **Attribute:** Jedes Attribut bekommt einen eigenen Block vor seinem `#define`.
  - Der erste Satz sagt, was es bewirkt.
  - Dann folgen Typ, Anwendbarkeit (`I`, `S`, `G`, `N`, `U` wie in den Autodocs), Vorgabewert
    und gültige Werte.
  - Die Attribute werden mit `@name` und `@{` … `@}` zu einer Gruppe zusammengefasst.
- **Methoden und Funktionen** werden ebenso dokumentiert, mit ihrer Nachrichtenstruktur bzw.
  ihren Parametern.
- **Die `$VER`-Zeile** bleibt als normaler Kommentar im Kopf stehen.

```c
/** @name Attributes */
/** @{ */

/**
 * @brief Directory shown as the root of the tree.
 *
 * The path is resolved to its full name and copied. Setting it reads the
 * directory's first level; NULL empties the tree. If the directory cannot
 * be read, the old tree stays and #DIRTREE_Status is #DIRTREE_ST_FAILED.
 *
 * Type: STRPTR. Applicability: I S G. Default: NULL.
 */
#define DIRTREE_Root        (DIRTREE_Dummy + 1)

/** @} */
```

## Werkzeug

- **Konfiguration:** `doxygen/Doxyfile.base` enthält die gemeinsame Grundkonfiguration
  (ISO-8859-1, C, nur Dokumentiertes, `static` eingeschlossen, alle Warnungen, nur HTML).
- **make-Regel:** `make/docs.mk` stellt `DOXYGEN_DOCS` bereit. Das Projekt legt damit seine
  Ziele an, z. B. `docs` für das ganze Programm und `docs-<klasse>` für den öffentlichen Header
  einer Klasse:

  ```make
  include $(DEVKIT)/make/docs.mk
  $(eval $(call DOXYGEN_DOCS,docs,TinyDev,1.0,src include,build/docs))
  ```

- **Ausgabe:** Das HTML landet unter `build/`, nie im Repository. Für ein Aminet-Paket kopiert
  `make dist` das HTML der Klassen ins Archiv (z. B. `Docs/<klasse>/`).
- **Installation:** Doxygen läuft auf dem Host (`apt install doxygen`, ab Version 1.9.5 für
  `WARN_IF_INCOMPLETE_DOC`).
