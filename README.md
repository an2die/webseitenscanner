
![Screenshot 2025-06-03 190956](https://github.com/user-attachments/assets/0d727af3-70c9-49c2-a289-a682ae65c38e)

Setup / Installation
Docker unter Windows 11
1. Installation der erforderlichen Softwarekomponenten

Docker Desktop
Installiere die aktuelle Version von Docker Desktop für Windows:
https://www.docker.com/products/docker-desktop
Docker Desktop stellt die Container-Laufzeitumgebung bereit und verwaltet Netzwerk- und Systemressourcen.

VcXsrv (X-Server)
Für die grafische Darstellung der Tkinter-Oberfläche benötigt Windows einen externen X-Server.
Download: https://vcxsrv.com/

2. Konfiguration des X-Servers

Starte XLaunch (im Installationsverzeichnis von VcXsrv).

Wähle im Assistenten „Multiple windows“.

Belasse die Display-Nummer auf 0.

Aktiviere die Checkbox „Disable access control“.

Klicke auf „Finish“, um den X-Server zu starten.

Diese Einstellungen erlauben dem Docker-Container, ohne Authentifizierung auf den X-Server zuzugreifen und die Fenster korrekt anzuzeigen.

3. Erstellen des Docker-Images
Öffne ein Terminal (PowerShell oder Eingabeaufforderung) und wechsle in das geklonte Projektverzeichnis:

powershell
Kopieren
Bearbeiten
cd C:\Users\<Benutzername>\webseitenscanner
docker build -t webseitenscanner .
Das Image enthält alle Abhängigkeiten und die Anwendung selbst.

4. Starten der Anwendung
Führe die Datei start_scanner.bat per Doppelklick aus.
Das Skript übernimmt automatisch:

Setzt die Umgebungsvariable DISPLAY auf host.docker.internal:0.0

Bindet config.json als Volume in den Container ein

Startet das Docker-Image webseitenscanner

Die Anwendung öffnet sich als Desktop-Fenster und kann wie gewohnt genutzt werden.

Docker unter Kali Linux
Installation der Docker Engine

bash
Kopieren
Bearbeiten
sudo apt update
sudo apt install docker.io
Alternativ findest du Anleitungen für andere Distributionen unter
https://docs.docker.com/engine/install/

Freigabe des X11-Displays für den Docker-Container

bash
Kopieren
Bearbeiten
xhost +local:docker
Dieser Befehl erlaubt allen Docker-Containern, Verbindungen zum X11-Server des aktuellen Benutzers herzustellen.

Erstellen des Docker-Images

bash
Kopieren
Bearbeiten
cd ~/webseitenscanner
docker build -t webseitenscanner .
Starten der Anwendung

bash
Kopieren
Bearbeiten
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -v "$(pwd)/config.json":/app/config.json \
  webseitenscanner
-e DISPLAY=$DISPLAY leitet die GUI-Befehle an den aktiven X-Server weiter.

-v "$(pwd)/config.json":/app/config.json bindet config.json als beschreibbares Volume ein, sodass Konfigurationsänderungen jederzeit möglich sind.

Alternative „Bare-Metal“ (ohne Docker)
Vorbereitung: Python und pip installieren

Linux (falls nicht bereits vorhanden):

bash
Kopieren
Bearbeiten
sudo apt update
sudo apt install python3 python3-pip
Windows:

Installer von https://python.org herunterladen und ausführen.

Im Setup „Add Python to PATH“ aktivieren.

Nach der Installation im Terminal prüfen:

bash
Kopieren
Bearbeiten
python --version
pip --version
Projektverzeichnis betreten

bash
Kopieren
Bearbeiten
cd webseitenscanner
Installation der Python-Abhängigkeiten

bash
Kopieren
Bearbeiten
pip install -r requirements.txt
Starten der Python-Anwendung

bash
Kopieren
Bearbeiten
python webseitenscanner.py
oder

bash
Kopieren
Bearbeiten
python3 webseitenscanner.py
Installation der Scanner-Tools
Im Rahmen der automatisierten Schwachstellenanalyse benötigt der Webseitenscanner verschiedene externe Werkzeuge. Unter Kali Linux sind viele dieser Tools bereits vorinstalliert oder über die Paketquellen verfügbar. Unter Windows ist oft eine manuelle Installation notwendig.
Die folgende Tabelle zeigt die gängigsten Tools und ihre Installationswege:

Tool	Kali Linux	Windows
Nmap	sudo apt install nmap	Offizieller Installer: https://nmap.org/download
Nikto	sudo apt install nikto	1. Perl-Laufzeit (z. B. Strawberry Perl) installieren
git clone https://github.com/sullo/nikto.git		
Dirsearch	git clone https://github.com/maurosoria/dirsearch.git	Python 3 installieren, dann:
git clone https://github.com/maurosoria/dirsearch.git		
SQLMap	sudo apt install sqlmap	git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev
SpiderFoot	sudo apt install spiderfoot	
oder		
git clone https://github.com/smicallef/spiderfoot.git	Python 3 +	
git clone https://github.com/smicallef/spiderfoot.git		
CMSeek	git clone https://github.com/Tuhinshubhra/CMSeeK.git	Python 3 +
git clone https://github.com/Tuhinshubhra/CMSeeK.git		
OWASP ZAP	sudo apt install zaproxy	Installer/ZIP: https://www.zaproxy.org/download

Hinweis: Viele Tools sind unter Kali Linux bereits vorinstalliert. Prüfe mit toolname --help, ob ein Tool vorhanden ist, bevor du es installierst.

Beispiel: Installation von Nmap unter Kali und Windows
Kali Linux

bash
Kopieren
Bearbeiten
sudo apt update
sudo apt install nmap
Windows

Rufe https://nmap.org/download auf

Lade den Windows-Installer herunter und führe ihn aus

Nmap (CLI) und Zenmap (GUI) stehen danach systemweit zur Verfügung
