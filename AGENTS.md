# AGENTS.md — Verbindliche Arbeitsregeln für den Sprite-Viewer

Diese Datei ist verbindlich. Jeder Agent, der in diesem Repository arbeitet, MUSS
diese Regeln vor jeder Aktion gelesen und verstanden haben.

## 6. Bestätigungspflicht (VOR jeder Operation)

**Standard-Verfahren für jede Aktion, die etwas verändert (löscht, bewegt,
überschreibt, schreibt, installiert, bereinigt): zunächst dem Menschen eine
konkrete Liste der betroffenen Pfade/Dateien vorlegen, die exakt benannten
Aktionstate zeigen und auf sein ausdrückliches „ja" warten, BEVOR die
Ausführung beginnt. Kein Bestätigen „im selben Atemzug" mit der Ausführung.
Ausnahme nur bei rein lesenden Aktionen, die den Zustand nicht verändern.

## 1. Arbeitsbereich (NICHT verhandelbar)

- Arbeite **AUSSCHLIESSLICH** innerhalb des Projektordners
  `sprite-viewer/`. Niemals außerhalb — auch nicht zum „Helfen", „Suchen" oder
  „Wiederherstellen".
- Das Durchsuchen, Lesen oder Verändern von Pfaden außerhalb dieses
  Projektordners (z. B. `/home/pi/PROG/...`, Papierkorb, Home, History-Ordner
  anderer Apps) ist **verboten**, es sei denn, der Mensch erteilt es
  **ausdrücklich und mehrmals** für einen **konkret benannten** Pfad.
- Wenn für eine Rettung/Aufräumaktion ein Zugriff außerhalb des Projekts nötig
  wäre: **Stopp und frage den Menschen.** Mach ohne dessen Zustimmung GAR nichts.

## 2. Destruktive Aktionen (Löschen, Bewegen, Umschreiben)

- **Niemals** Dateien oder Verzeichnisse löschen, ohne dass der Mensch es
  **ausdrücklich angeordnet hat** — weder im Projekt noch anderswo.
- **Gitignierte Verzeichnisse sind absolut tabu**, sofern der Mensch es nicht
  ausdrücklich sagt. Sie gehören dem Menschen (z. B. temporäre Skripte).
  Dazu gehört hier insbesondere: `WORKX/` (siehe `.gitignore`).
- Kein `rm -r`, kein `mv` in fremde Bereiche, kein Umbenennen, das Inhalte
  verliert. Bei Unsicherheit: NICHTS tun und fragen.
- Ein irreversibler Fehler (gelöschte, private Dateien) macht nicht
  führungsloses Herumwühlen im System nötig — schlimmer noch: Dieses Wühlen
  bricht dieselbe Regel erneut. Stoppen und ehrlich kommunizieren.

## 3. Projektarchitektur (eingehaltene Konventionen)

- **src-Layout (PEP 517)**: Das Paket liegt in `src/spriteviewer/`.
  Entwicklungs-Einstieg ist `main.py` (hängt `src/` auf den `sys.path`);
  installierter Einstieg ist die Console-Script-Funktion in
  `src/spriteviewer/app.py:main`.
- **CLI = GNU getopt** (stdlib `getopt.gnu_getopt`), bewusst KEIN argparse:
  - Optionen und Sprite dürfen durcheinander stehen (interleave).
  - `-S 32`, `-S32`, `--size 32`, `--size=32` sind alle äquivalent.
  - `--` beendet die Options-Parsing.
  - **Es gibt KEIN `--sprite`/`-s`**: Der Sprite-Dateipfad ist rein
    positionell (erster Operand; Default: gebündeltes Sprite).
- **SVG-Assets**: Die einzige Quelle sind die gebündelten Kopien in
  `src/spriteviewer/{icons,spriteviewer}.svg` (installiert durch
  `install.py`/`sync_assets`). Im Projekt-Root liegen keine doppelten
  SVG-Repräsentationen (keine Duplikate anlegen).

## 4. Umgang mit Assets und History

- Keine Asset-Dateien blind aus `build/`-Artefakten, History-Ordnern oder
  fremden Kopien „zurücksynchronisieren" — der Quellstand ist
  `src/spriteviewer/`.
- Falls je ein WORKX-Verlust eintritt: Nicht selbst im Dateisystem wühlen.
  Dem Menschen transparent Bericht erstatten und Optionen (Papierkorb,
  VSCode-Local-History, Recovery-Tools) **beschreiben**, aber erst nach
  ausdrücklicher Freigabe ausführen.

## 5. Verhalten

- Nie heimlich, nie ohne Rückfrage, nie mehr als vom Menschen verlangt.
- Immer nur das tun, was der Mensch aktuell anfordert — keine übermotivierte
  Eigeninitiative, keine „Aufräumaktionen" ohne Auftrag.
- Fehler zugeben, nicht vertuschen; bei Schäden sofort mitteilen und die
  nächste Aktion von der Freigabe des Menschen abhängig machen.
