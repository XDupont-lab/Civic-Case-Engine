# Agentic Workspace for Base Administration (AWB)

[Nederlands](README.md)

> **Definition.** Agentic Workspace for Base Administration. The ketengrootboek is the centre: money is entered twice, a handover once, and it stays open until the other side books it.

Ketengrootboek is the chain ledger. Money already has a double entry. A handover between people is entered once. That entry stays open until the receiving side books the counter-entry. Two green counters without that counter-entry are not a close.

The workspace keeps one picture across care, desks, and money. It runs on the person's own computer. The case file, the letters, and the names stay out of git. The person reads a draft and gives the go-ahead before anything is sent. While a conversation with a local desk is still open, the program does not send a formal notice of default and does not name a penalty amount.

The build standard is [APPLICATIE_SPECIFICATIE.md](APPLICATIE_SPECIFICATIE.md), in Dutch. The window is called Civic Helper. The repository is still named `Civic-Case-Engine`.

The longer architecture notes in this repository are in Dutch. This file is the door.

## Start

1. Clone the repository and enter it.
   ```bash
   git clone https://github.com/XDupont-lab/Civic-Case-Engine.git
   cd Civic-Case-Engine
   ```
2. On Windows, `CivicHelper.cmd` opens the window. On Linux, `hulp/start_venster.sh` opens the same window.
3. A clean computer starts with `ontkiem.py`. One ordinary mail address is enough to begin. A model key stays in the environment. The window does not ask for one.
4. `START.cmd` and `start_linux.sh` are the builder menu. That menu is not the door.

Whether a handover closes is tested by `Ketengrootboek/sluiting.py`. If the counter-entry is missing, the entry stays open. The public example is called Voorbeeldstad. A path into a personal case file does not belong in `interfaces.json`.

## What sits where

| Piece | Role |
|---|---|
| `gui/` | Civic Helper 0.3 multi-agent Tafel interface (PyQt6, indexer, archiver, dispatch). |
| `hulp/` | The lightweight classic window. `venster.py` draws it. `lus.py` talks to the local agent. |
| `Ketengrootboek/` | The chain ledger. `sluiting.py` tests the counter-entry. |
| `_engine/` | Clocks, timeline, gates, and the glue check. No vector search. A repeated word is not a link. |
| `APPLICATIE_SPECIFICATIE.md` | What the program is for, and the order in which it is built. |
| `werk/` | The person's case. Git ignores it. |

A local case folder can be pointed at with the environment variable `CCE_DOSSIER`. The program does not ship a path to one.
