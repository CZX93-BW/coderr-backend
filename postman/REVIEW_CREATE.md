# Coderr – Review CREATE

## Dateien

- `Coderr_Review_CREATE.postman_collection.json`
- `Coderr_Review_CREATE_Local.postman_environment.json`
- `REVIEW_CREATE.md`

## Start und Durchführung

1. Die drei Dateien in den Ordner `postman` deines Backend-Projekts kopieren.
2. In einem Terminal mit aktivierter virtueller Umgebung `python manage.py runserver`
   ausführen und den Server laufen lassen.
3. Beide JSON-Dateien in Postman importieren.
4. Environment **Coderr Review Create Local** auswählen.
5. Collection **Coderr Review CREATE** über **Run collection** starten.
6. Eine Iteration, alle Requests aktiviert und ursprüngliche Reihenfolge beibehalten.

Erwartet: **47 Requests, 133 bestandene Prüfungen, keine Fehler**.
Keine Passwörter, Tokens, Benutzer-IDs oder Dateien manuell auswählen.
`base_url` enthält `/api` und keinen abschließenden Slash.

## Abdeckung

- POST `/api/reviews/`: Kunden erstellen Bewertungen mit Status 201.
- Alle ganzzahligen Ratings 1 bis 5 kommen in erfolgreichen Requests vor.
- Keine vorherige Bestellung erforderlich; die Collection erzeugt keine Bestellungen.
- Unterschiedliche Kunden dürfen denselben Anbieter bewerten.
- Derselbe Kunde darf unterschiedliche Anbieter bewerten.
- Zweite Bewertung derselben Kombination liefert 400, auch mit verändertem Inhalt.
- Bewertender stammt aus dem Token; fremde Reviewer-ID wird ignoriert.
- Clientseitige ID und Zeitstempel werden nicht übernommen.
- Exakte sieben Antwortfelder, ganzzahliges Rating, Teilnehmer, Text und Zeitstempel.
- Ungültige Ratings: negative Werte, 0, 6, Dezimalzahl, Text, leer, null,
  Boolean sowie Zeichenketten NaN und Infinity.
- Fehlende, leere und null-Pflichtfelder; ungültige Beschreibungstypen und Leerzeichen.
- Ungültige Anbieter-ID, Kunden-ID und unbekannter Anbieter liefern 400.
- Ungültige JSON-Grundformen (null, Array, String) liefern 400.
- Business darf keine Bewertung erstellen: 403; fehlender/ungültiger Token: 401.
- Nach allen ungültigen Eingaben gelingt eine gültige Bewertung mit demselben
  Kunden-Anbieter-Paar, das bei den Validierungsfehlern benutzt wurde.

## Testdaten und Wiederholbarkeit

Jeder vollständige Lauf registriert fünf neue Benutzer mit eindeutigem Namenssuffix:
**drei Kunden und zwei Anbieter**. Bei erfolgreichem Lauf entstehen **fünf Bewertungen**.
Diese Daten bleiben in deiner lokalen Datenbank. Die Collection löscht nichts und
verändert keine bestehenden Benutzer, Angebote oder Bestellungen.
Die unbekannte Anbieter-ID 2147483647 muss lokal unbenutzt sein.

Bei jedem vollständigen Neustart werden die eigenen dynamischen Collection-Variablen
zurückgesetzt. Die Vorbereitung liefert die neuen IDs und Tokens automatisch.
Einzelne Requests hängen von den vorherigen Schritten ab; nicht isoliert wiederholen.
Fehlgeschlagene Registrierungen und eine fehlgeschlagene erste Review-Erstellung
stoppen den Runner, um Folgefehler durch fehlende Testdaten zu vermeiden.

## Prüfgrenzen

Der aktuelle Stand bietet noch keinen GET-Endpunkt für Reviews. Deshalb liest diese
Collection die gespeicherten Bewertungen nicht nachträglich aus. Dass ein Duplikat
bestehende Inhalte und Zeitstempel unverändert lässt und ungültige Eingaben keine
Datensätze erzeugen, prüfen bereits die Django-Tests direkt in der Datenbank.
Nicht als zusätzliche HTTP-Abdeckung ausgeben: Benutzer ohne Profil und parallele
Schreibzugriffe werden hier nicht vorbereitet bzw. simuliert.

Collection-Struktur und Skripte wurden mit kontrollierten Antworten und gezielt
fehlerhaften Antworten geprüft. Der echte HTTP-Lauf erfolgt auf deinem Rechner.

## Fehler untersuchen

Im Runner den ersten fehlgeschlagenen Request öffnen und Status sowie Response-Body
prüfen. Bei einem Verbindungsfehler Django-Server und ausgewähltes Environment prüfen.
Bei Folgefehlern zuerst die Registrierung und die erste Review-Erstellung untersuchen.
