# Coderr Review LIST

Die Collection prüft GET `/api/reviews/` über HTTP. Ein vollständiger Lauf umfasst 48 Requests und 162 Prüfungen.

## Lokal ausführen

1. Die drei Dateien aus dem ZIP-Ordner `postman` in den gleichnamigen Ordner deines Backend-Projekts kopieren.
2. In CMD mit aktivierter virtueller Umgebung `python manage.py runserver` starten und das Terminal geöffnet lassen.
3. In Postman die Collection `Coderr_Review_LIST.postman_collection.json` und das Environment `Coderr_Review_LIST_Local.postman_environment.json` importieren.
4. **Coderr Review List Local** auswählen. Die Variable `base_url` ist auf `http://127.0.0.1:8000/api` eingestellt.
5. **Coderr Review LIST** im Collection Runner mit allen Requests in Originalreihenfolge und einer Iteration ausführen.

## Daten pro Lauf

Die Registrierung erzeugt drei Kunden und zwei Anbieter mit einem eindeutigen Namenssuffix. Tokens und IDs werden automatisch gesetzt. Die Collection merkt sich die IDs der bereits vorhandenen Bewertungen und legt fünf neue Bewertungen an. Diese fünf Benutzer und fünf Bewertungen bleiben in der lokalen Datenbank. Während des Laufs die lokale Review-Datenbank für die Collection reservieren, damit die erwarteten IDs stabil bleiben. Für den Test einer unbekannten ID wird 2147483647 als lokal unbenutzt vorausgesetzt.

## Geprüftes Verhalten

- Kunden und Anbieter können eigene sowie fremde Bewertungen als JSON-Array abrufen.
- Die vollständige Liste umfasst die beim Start erfassten IDs und alle neu angelegten Bewertungen. Die sieben Antwortfelder und die Werte der Testbewertungen einschließlich Zeitstempeln werden geprüft.
- Anbieter- und Reviewerfilter funktionieren einzeln und kombiniert. Kombinationen ohne Treffer und unbekannte positive IDs liefern ein leeres Array.
- Reihenfolge nach Rating oder Aktualisierungszeitpunkt wird jeweils auf- und absteigend geprüft. Standard ist der jüngste Aktualisierungszeitpunkt zuerst. Bei Gleichstand entscheidet im implementierten Backend die höhere ID.
- Leere Filter, Leerzeichen, kombinierte Filter und Sortierung werden geprüft.
- Ungültige ID-Filter oder Sortierwerte liefern 400 mit zugehörigem Feld. Fehlender oder ungültiger Token liefert 401.
- Gültige Lesezugriffe nach den Fehlerfällen liefern weiterhin die erwarteten Daten.

## Bei einem Fehler

Im Runner den ersten roten Request öffnen und HTTP-Status, Response-Body und fehlgeschlagene Prüfung anschauen. Bei einem Verbindungsfehler Server und Environment prüfen. Zum Wiederholen die vollständige Collection neu starten.

Die Skripte wurden mit simulierten Antworten für leere und vorbefüllte Ausgangsdaten sowie neun gezielt fehlerhaften Varianten geprüft. Der HTTP-Test gegen Django erfolgt im lokalen Runner.
