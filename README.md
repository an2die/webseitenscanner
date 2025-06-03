WebseitenScanner
![Screenshot 2025-06-03 190956](https://github.com/user-attachments/assets/0d727af3-70c9-49c2-a289-a682ae65c38e)

Setup / Installation
Docker unter Windows 11
Nach dem Klonen des Repositories erfolgen die notwendigen Installations- und Startschritte wie folgt:
1. Installation der erforderlichen Softwarekomponenten
•	Docker Desktop: Installieren Sie die aktuelle Version von Docker Desktop für Windows, verfügbar unter https://www.docker.com/products/docker-desktop/.
Docker Desktop stellt die Container-Laufzeitumgebung bereit und verwaltet alle für den Betrieb notwendigen Netzwerk- und Systemressourcen.
•	VcXsrv (X-Server): Für die grafische Darstellung der Tkinter-Oberfläche wird ein externer X-Server benötigt, da Windows selbst keine native X11-Unterstützung bietet.
Die Installation erfolgt über den offiziellen Download-Link https://vcxsrv.com/.
2. Konfiguration des X-Servers
•	Starten Sie XLaunch (im Installationsverzeichnis von VcXsrv enthalten).
•	Wählen Sie im Assistenten die Option „Multiple windows“.
•	Belassen Sie die Display-Nummer auf 0.
•	Aktivieren Sie die Checkbox „Disable access control“.
•	Klicken Sie auf „Finish“, um den X-Server zu starten.
Diese Einstellungen gewährleisten, dass der Docker-Container ohne Authentifizierung auf den X-Server zugreifen kann und die Fenster korrekt angezeigt werden.
3. Erstellen des Docker-Images
•	Öffnen Sie ein Terminal (PowerShell oder Eingabeaufforderung).
•	Navigieren Sie in das Verzeichnis, das das geklonte Repository enthält (z. B. cd C:\Users\Benutzername\webseitenscanner).
•	Stellen Sie sicher, dass Docker Desktop läuft.
•	Bauen Sie das Docker-Image mit folgendem Befehl: 
„docker build -t webseitenscanner .“
Das Image enthält alle Abhängigkeiten und die Anwendung selbst.
4. Starten der Anwendung
•	Führen Sie die bereitgestellte Datei start_scanner.bat per Doppelklick aus.
•	Das Skript übernimmt automatisch alle notwendigen Einstellungen:
o	Die Umgebungsvariable DISPLAY wird korrekt gesetzt (host.docker.internal:0.0).
o	Die Konfigurationsdatei config.json wird als Volume in den Container eingebunden.
o	Das Container-Image webseitenscanner wird gestartet.
Der Benutzer muss am Startskript keine Anpassungen vornehmen.
Die Anwendung öffnet sich als Desktop-Fenster und kann wie gewohnt genutzt werden.

Docker unter Kali Linux 
Nach dem Klonen des Repositorys erfolgen die folgenden Schritte zur Einrichtung und zum Start der Anwendung:
1. Installation der Docker Engine
Installieren Sie zunächst die aktuelle Version der Docker Engine mit dem Paketmanager Ihrer Linux-Distribution.
Beispielsweise unter Kali:
„sudo apt update“
„sudo apt install docker.io“
Alternativ steht die Installationsanleitung für weitere Distributionen unter https://docs.docker.com/engine/install/ zur Verfügung.
2. Freigabe des X11-Displays für den Docker-Container
Damit grafische Anwendungen innerhalb des Containers auf den Host-Bildschirm zeichnen können, muss der Zugriff auf den lokalen X11-Server explizit erlaubt werden:
„xhost +local:docker“
Dieser Befehl gestattet allen Docker-Containern, Verbindungen zum X11-Server des aktuellen Benutzers herzustellen.
3. Erstellen des Docker-Images
Navigieren Sie in das geklonte Projektverzeichnis:
„cd ~/webseitenscanner“
Bauen Sie das Docker-Image auf Grundlage der mitgelieferten Dockerfile:
„docker build -t webseitenscanner .“
4. Starten der Anwendung
Starten Sie die Anwendung mit folgendem Befehl:
„docker run --rm \
           -e DISPLAY=$DISPLAY \
           -v "$(pwd)/config.json":/app/config.json \
           Webseitenscanner“
Die Umgebungsvariable DISPLAY sorgt dafür, dass der Container seine GUI an den aktuell aktiven X-Server überträgt.
Die Datei config.json wird als beschreibbares Volume in den Container eingebunden, wodurch Konfigurationsänderungen jederzeit möglich sind.

Alternative Bare-Metal 
Eine weitere Möglichkeit ist es das Python Script direkt auszuführen mit der Installeirtem Python ohne Docker auszuführen.
1. Vorbereitung: Python und pip installieren
Linux: In der Regel sind Python 3 und pip bereits vorinstalliert. Falls nicht, können sie über den Paketmanager installiert werden:
„sudo apt update“
„sudo apt install python3 python3-pip“
Windows: Den offiziellen Installer von python.org herunterladen und ausführen.
Wichtig: Beim Setup das Häkchen bei „Add Python to PATH“ setzen.
Nach der Installation im Terminal prüfen:
„python –version“
„pip –version“
2. Projektverzeichnis betreten
Navigieren Sie in das Verzeichnis, das das jeweilige Python-Tool enthält, also in das geklonte Repository:
„cd webseitenscanner“
3. Installation der Python-Abhängigkeiten mit pip
In dem Ordner befindet sich die requirements.txt, in der sämtliche benötigten Python-Bibliotheken gelistet sind.
Die Installation erfolgt mit:
„pip install -r requirements.txt“
4. Starten der Python-Anwendung
Das eigentliche Python-Tool wird über ein zentrales Skript gestartet:
„python webseitenscanner.py“
 oder
„python3 websietenscanner.py“


Installation der Tools
Im Rahmen der automatisierten Schwachstellenanalyse werden verschiedene spezialisierte Werkzeuge eingesetzt. Ohne eine Installation der Tools funktioniert der Webseitenscanner nicht. Während in Kali Linux als dedizierter Security-Distribution viele dieser Tools bereits vorinstalliert oder unmittelbar über die offiziellen Paketquellen verfügbar sind, ist unter Windows häufig eine manuelle Installation und Konfiguration erforderlich. Die nachfolgende Übersicht beschreibt die relevanten Werkzeuge sowie deren Installationswege unter beiden Betriebssystemen.
1. Nmap
Nmap (Network Mapper) dient der Netzwerkerkennung und dem Sicherheits-Scanning.
•	Kali Linux: Nmap ist in der Regel bereits vorinstalliert. Sollte dies nicht der Fall sein, kann die Installation über den Paketmanager erfolgen:
sudo apt update
sudo apt install nmap
•	Windows:
Für Windows steht ein offizieller Installer zur Verfügung (https://nmap.org/download.html). Nach der Installation sind sowohl das Kommandozeilentool als auch das grafische Frontend (Zenmap) systemweit verfügbar.
2. Nikto
Nikto ist ein in Perl implementierter Webserver-Scanner zur Identifikation unsicherer Konfigurationen und bekannter Schwachstellen.
•	Kali Linux: Nikto ist Teil der offiziellen Paketquellen und in den meisten Fällen vorinstalliert. Die Installation erfolgt andernfalls wie folgt:
sudo apt update
sudo apt install nikto
•	Windows:
Für den Einsatz von Nikto unter Windows ist zunächst die Installation einer Perl-Laufzeitumgebung (z. B. Strawberry Perl) erforderlich. Anschließend kann das offizielle Repository von GitHub geklont und das Tool mittels Perl gestartet werden:
git clone https://github.com/sullo/nikto.git
3. Dirsearch
Dirsearch ist ein Python-basiertes Tool zur gezielten Erkennung von Verzeichnissen und Dateien auf Webservern (Brute-Force).
•	Kali Linux: Dirsearch ist meist nicht vorinstalliert, kann jedoch direkt aus dem offiziellen GitHub-Repository bezogen werden. Voraussetzung ist eine funktionierende Python-3-Umgebung:
git clone https://github.com/maurosoria/dirsearch.git
•	Windows:
Auch unter Windows wird zunächst Python 3 benötigt. Nach dessen Installation (über python.org) kann das Tool wie unter Linux mit Git geklont und gestartet werden:
git clone https://github.com/maurosoria/dirsearch.git
4. SQLMap
SQLMap ist ein etabliertes Werkzeug zur automatisierten Erkennung und Ausnutzung von SQL-Injection-Schwachstellen.
•	Kali Linux: SQLMap ist standardmäßig vorinstalliert oder über den Paketmanager beziehbar:
sudo apt update
sudo apt install sqlmap
•	Windows:
Für Windows empfiehlt sich der Bezug der jeweils aktuellen Version über GitHub:
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev
5. SpiderFoot
SpiderFoot ist ein Framework zur automatisierten OSINT-Erhebung (Open Source Intelligence).
•	Kali Linux: SpiderFoot kann über die Paketquellen installiert werden:
sudo apt update
sudo apt install spiderfoot
Alternativ steht das aktuelle Repository auf GitHub zur Verfügung:
git clone https://github.com/smicallef/spiderfoot.git
•	Windows:
Nach Installation von Python 3 und Git erfolgt die Einrichtung analog:
git clone https://github.com/smicallef/spiderfoot.git
6. CMSeek
CMSeek dient der automatisierten Erkennung von Content-Management-Systemen (CMS) sowie der Identifikation spezifischer Schwachstellen.
•	Kali Linux: Nicht vorinstalliert, aber problemlos über das offizielle Repository verfügbar:
git clone https://github.com/Tuhinshubhra/CMSeeK.git
•	Windows:
Nach Installation von Python und Git identisch wie unter Linux:
git clone https://github.com/Tuhinshubhra/CMSeeK.git
7. OWASP ZAP (Zed Attack Proxy)
OWASP ZAP ist ein Framework zur Webanwendungsanalyse und für Penetrationstests.
•	Kali Linux: ZAP ist über die offiziellen Paketquellen installierbar:
sudo apt update
sudo apt install zaproxy
•	Windows:
Die aktuelle Version kann als Installationspaket oder ZIP-Datei von der offiziellen Website (https://www.zaproxy.org/download/) bezogen werden. Nach der Installation steht ZAP über das Startmenü oder das Kommandozeilentool zap.bat zur Verfügung.

