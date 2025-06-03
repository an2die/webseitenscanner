
![Screenshot 2025-06-03 190956](https://github.com/user-attachments/assets/0d727af3-70c9-49c2-a289-a682ae65c38e)

Setup / Installation

Docker unter Windows 11

Installation der erforderlichen Softwarekomponenten

Docker Desktop
Installiere die aktuelle Version von Docker Desktop für Windows (https://www.docker.com/products/docker-desktop).
Docker Desktop stellt die Container-Laufzeitumgebung bereit und verwaltet Netzwerk- und Systemressourcen.

VcXsrv (X-Server)
Für die grafische Darstellung der Tkinter-Oberfläche wird unter Windows ein externer X-Server benötigt (Download: https://vcxsrv.com/).

Konfiguration des X-Servers

Starte XLaunch (im Installationsverzeichnis von VcXsrv).

Wähle im Assistenten „Multiple windows“.

Belasse die Display-Nummer auf 0.

Aktiviere die Checkbox „Disable access control“.

Klicke auf „Finish“, um den X-Server zu starten.
Diese Einstellungen erlauben dem Docker-Container, ohne Authentifizierung auf den X-Server zuzugreifen und die Fenster korrekt anzuzeigen.

Erstellen des Docker-Images

Öffne ein Terminal (PowerShell oder Eingabeaufforderung)

Wechsle in das geklonte Projektverzeichnis, zum Beispiel:
cd C:\Users<Benutzername>\webseitenscanner

Stelle sicher, dass Docker Desktop läuft

Baue das Docker-Image mit folgendem Befehl:
docker build -t webseitenscanner .
Das Image enthält alle Abhängigkeiten und die Anwendung selbst.

Starten der Anwendung

Führe die Datei start_scanner.bat per Doppelklick aus.
Das Skript übernimmt automatisch:
• Es setzt die Umgebungsvariable DISPLAY auf host.docker.internal:0.0
• Es bindet config.json als Volume in den Container ein
• Es startet das Docker-Image webseitenscanner
Die Anwendung öffnet sich als Desktop-Fenster und kann wie gewohnt genutzt werden.

Docker unter Kali Linux

Installation der Docker Engine

Führe folgende Befehle aus:
sudo apt update
sudo apt install docker.io
Alternativ findest du Anleitungen für andere Distributionen unter https://docs.docker.com/engine/install/.

Freigabe des X11-Displays für den Docker-Container

Erlaube allen Containern den Zugriff auf den X11-Server:
xhost +local:docker

Erstellen des Docker-Images

Wechsle in das geklonte Projektverzeichnis:
cd ~/webseitenscanner

Baue das Docker-Image:
docker build -t webseitenscanner .

Starten der Anwendung

Führe im Terminal aus:
docker run --rm -e DISPLAY=$DISPLAY -v "$(pwd)/config.json":/app/config.json webseitenscanner
Die Umgebungsvariable DISPLAY leitet die GUI-Ausgabe an den X11-Server weiter.
Das Volume bindet config.json in den Container, sodass Konfigurationsänderungen erhalten bleiben.

Alternative „Bare-Metal“ (ohne Docker)

Vorbereitung: Python und pip installieren

Unter Linux (falls nicht bereits vorhanden):
sudo apt update
sudo apt install python3 python3-pip

Unter Windows:
• Installer von https://python.org herunterladen und ausführen
• Im Setup „Add Python to PATH“ aktivieren
• Nach der Installation im Terminal prüfen:
python --version
pip --version

Projektverzeichnis betreten

Wechsle in das Verzeichnis des geklonten Repositories:
cd webseitenscanner

Installation der Python-Abhängigkeiten

Installiere alle benötigten Bibliotheken:
pip install -r requirements.txt

Starten der Python-Anwendung

Führe aus:
python webseitenscanner.py
oder
python3 webseitenscanner.py

Installation der Scanner-Tools

Im Rahmen der automatisierten Schwachstellenanalyse benötigt der Webseitenscanner verschiedene externe Werkzeuge.
Unter Kali Linux sind viele Tools bereits vorinstalliert. Unter Windows muss oft manuell installiert werden.
Nachfolgend die wichtigsten Tools und ihre Installationswege:

Nmap

Kali Linux:
sudo apt install nmap

Windows:
Offizieller Installer von https://nmap.org/download herunterladen und ausführen

Nikto

Kali Linux:
sudo apt install nikto

Windows:
• Zuerst eine Perl-Laufzeit (z. B. Strawberry Perl) installieren
• Danach:
git clone https://github.com/sullo/nikto.git

Dirsearch

Kali Linux:
git clone https://github.com/maurosoria/dirsearch.git

Windows:
• Installiere Python 3
• Dann:
git clone https://github.com/maurosoria/dirsearch.git

SQLMap

Kali Linux:
sudo apt install sqlmap

Windows:
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev

SpiderFoot

Kali Linux:
sudo apt install spiderfoot
oder
git clone https://github.com/smicallef/spiderfoot.git

Windows:
• Installiere Python 3
• Dann:
git clone https://github.com/smicallef/spiderfoot.git

CMSeek

Kali Linux:
git clone https://github.com/Tuhinshubhra/CMSeeK.git

Windows:
• Installiere Python 3
• Dann:
git clone https://github.com/Tuhinshubhra/CMSeeK.git

OWASP ZAP

Kali Linux:
sudo apt install zaproxy

Windows:
Installer oder ZIP von https://www.zaproxy.org/download herunterladen und ausführen

Hinweis: Viele Tools sind auf Kali Linux bereits vorinstalliert. Prüfe mit toolname --help, ob sie vorhanden sind, bevor du sie installierst.
Rufe https://nmap.org/download auf

Lade den Windows-Installer herunter und führe ihn aus

Nmap (CLI) und Zenmap (GUI) stehen danach systemweit zur Verfügung
