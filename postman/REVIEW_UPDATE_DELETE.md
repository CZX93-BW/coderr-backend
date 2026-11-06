# Coderr Review UPDATE DELETE

Die Collection prüft PATCH und DELETE auf `/api/reviews/{id}/`. Sie liest den gespeicherten Zustand über `GET /api/reviews/?business_user_id=...` zurück.

## Lokal ausführen

1. Die drei Dateien aus dem ZIP-Ordner `postman` in den Ordner `postman` deines Backend-Projekts übernehmen.
2. Im Backend-Terminal mit aktiver virtueller Umgebung `python manage.py runserver` starten.
3. Beide JSON-Dateien in Postman importieren und **Coderr Review Update Delete Local** auswählen.
4. **Coderr Review UPDATE DELETE** mit **Run collection** starten. Eine Iteration wählen und alle Requests in Originalreihenfolge ausführen.

Erwartet werden **60 Requests und 143 bestandene Prüfungen**. Das Environment verwendet `http://127.0.0.1:8000/api`. Die Registrierung setzt alle IDs und Tokens automatisch.

## Testfälle

- Der Verfasser ändert Rating und Beschreibung einzeln und gemeinsam. Die gültigen Grenzen 1 und 5 werden geprüft.
- Beim Versuch, Teilnehmer, ID und Zeitstempel zusammen mit einem gültigen Rating zu überschreiben, wird nur das Rating übernommen. Der Server setzt den Änderungszeitpunkt.
- Ungültige Ratings und Beschreibungen sowie ein leeres PATCH oder ausschließlich geschützte Felder liefern 400. Die anschließende Listenabfrage vergleicht auch die gespeicherten Zeitstempel.
- Ein anderer Kunde, der bewertete Anbieter und ein fremder Anbieter erhalten bei PATCH und DELETE jeweils 403. Fehlende und ungültige Tokens führen zu 401.
- Nach Zurückweisungen kann der Verfasser seine Bewertung weiterhin bearbeiten.
- Erfolgreiches Löschen liefert 204 mit leerem Body. Die übrigen Bewertungen werden anschließend über beide Anbieterprofile geprüft.
- Weitere Schreib- und Löschversuche auf die eben gelöschte ID liefern 404.

## Testdaten

Jeder Lauf registriert zwei Kunden und zwei Anbieter mit eindeutigen Namen und erzeugt drei Bewertungen. Bei vollständigem erfolgreichem Lauf löschen die jeweiligen Verfasser alle drei Testbewertungen. Vier Testkonten bleiben in der lokalen Datenbank. Bei Abbruch können auch Testbewertungen zurückbleiben. Zum Wiederholen die Collection von vorn starten, damit die Vorbereitung neue IDs erzeugt.

Bei einem roten Ergebnis im Runner den ersten fehlgeschlagenen Request öffnen und dessen tatsächlichen Status sowie Response-Body prüfen. Ein nachträglich einzeln abgesendeter Request verwendet nach dem Cleanup gegebenenfalls eine bereits gelöschte Bewertung.

Die Skripte wurden mit simulierten Antworten und sechs Fehlerfällen geprüft. Der HTTP-Lauf erfolgt gegen dein lokales Backend.
