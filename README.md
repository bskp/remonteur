filmton
=======


Sonstige hilfreiche Software
----------------------------
 
- Final Cut Pro
- daVinci Resolve


Installation für Mac
------------


### Benötigte Kommandozeilen-Tools installieren

*Homebrew* kann das schnell und einfach erledigen (MacOs-Paketmanager). [Auf der Website](https://brew.sh) steht alles Notwendige zur Installation. Sobald diese abgeschlossen ist:

1. Installiere scipy und numpy mit
    - ``$ brew install scipy``
    - ``$ brew install numpy``
2. Installiere alles benötigten Python-Module in einem Rutsch mit:
    - ``$ pip install -r requirements.txt``

    
### Filme bündeln
Das Tool erwartet einen Ordner, in welchem für jeden Film ein Unterordner existiert. Darin befinden sich der Film selbst (.mkv, .mp4 oder .avi) und eine Untertitel-Datei (.srt, kann von ``subliminal`` geholt werden):

- Filme/
   - Pocahontas/ 
     - pocahontas.mkv
     - pocahontas.srt
     - *snippets/* (Dialogfetzen, wird vom Tool erzeugt)
   - Der König der Löwen/
     - lionking.avi
     - lionkingDe.srt
     - *snippets/*

   - *lines.db* (Datenbank, wird vom Tool erstellt)

### Filme verarbeiten
``./rescan.py <Filme-Verzeichnis>``

Entwickeln
==========

Das Gui ist eine electron-Applikation. 

``cd filmton``

``npm install``

``npm run dist``erzeugt app