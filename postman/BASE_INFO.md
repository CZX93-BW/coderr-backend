# Coderr Base Info

## Lokaler Lauf

1. Die drei Dateien aus dem ZIP-Ordner `postman` in den gleichnamigen Backend-Ordner kopieren.
2. In CMD mit aktivierter virtueller Umgebung `python manage.py runserver` starten.
3. Beide JSON-Dateien in Postman importieren. **Coderr Base Info Local** auswählen.
4. **Coderr Base Info** mit einer Iteration und allen Requests in Originalreihenfolge starten.

Erwartet werden **36 Requests und 101 bestandene Prüfungen**. Der Server läuft unter `http://127.0.0.1:8000`. Zugangsdaten werden während des Laufs erzeugt.

## Kontrollierte Ausgangsdaten und Berechnung

Im normalen Lauf bleibt `expect_empty_start=false`. Die Collection liest zu Beginn die einzelnen Ratings über die Review-Liste, zählt die Geschäftsprofile über die Profilliste und liest die Gesamtzahl der Angebote aus der paginierten Angebotsliste. Der Erwartungswert für den Durchschnitt wird aus der Summe aller einzelnen Ratings berechnet. Während des Laufs Änderungen an diesen Daten ausschließlich über den Runner vornehmen.

Wenn ein separater lokaler Server mit frisch migrierter leerer Testdatenbank bereitsteht, kann `expect_empty_start=true` gesetzt werden. Dann muss bereits der erste anonyme Aufruf exakt vier Nullwerte liefern. Bei einer befüllten Entwicklungsdatenbank den Standardwert verwenden. Der Django-Test für den Leerzustand läuft separat in einer frischen Testdatenbank.

Zwei neue Kunden und zwei neue Anbieter werden registriert. Die Kundenregistrierung muss den Anbieterzähler erhalten, die beiden Anbieter erhöhen ihn um zwei. Drei Angebote bei zwei Anbietern erhöhen den Angebotszähler um drei. Für drei neue Bewertungen mit 5, 4 und 1 Sternen berechnet der Runner den Gesamtmittelwert, nach der Änderung von 1 auf 5 erneut und nach der Löschung nochmals. Bei anfangs leerer Review-Tabelle sind die Sollwerte 3,3, dann 4,7, dann 4,5. Ein abgelehntes Rating von 6 erhält alle Kennzahlen. Anonyme und angemeldete Leser erhalten dieselben globalen Werte.

Bei vollständigem Erfolg werden alle drei Testangebote und drei Testbewertungen durch ihre jeweiligen Verfasser gelöscht. **Vier Benutzerkonten bleiben bestehen, davon zwei Anbieter.** Beim letzten Request liegen Angebotszahl, Reviewanzahl und Rating wieder beim Ausgangswert. Für einen erneuten Lauf mit derselben Datenbank `expect_empty_start=false` wählen.

## Frontend-Abnahme

Nach dem Lauf ausgeloggt die Startseite neu laden und die Kennzahlen mit dem letzten anonymen Request `STATS | Final public summary` vergleichen. Bei Abweichungen zuerst prüfen, ob Frontend und Runner denselben Backend-Server verwenden.

## Prüfstand

Die Postman-Skripte wurden mit simulierten Antworten für eine leere und drei vorbefüllte Ausgangslagen geprüft, darunter Rundungsgrenzfälle. Sechs eingebaute Fehler wurden erkannt. Den echten HTTP-Lauf dokumentiert das Ergebnis des lokalen Runners.

## Zuordnung der API-Operationen

Je ein vorhandener Postman-Request pro dokumentierter Operation. Die Tabelle dient als Inventar der Collections. Dieses ZIP enthält die Statistik-Collection.

| ID | Operation | Collection und Beispielrequest |
|---|---|---|
| E01 | `POST /api/registration/` | Coderr Backend · E01-01 – Register customer |
| E02 | `POST /api/login/` | Coderr Backend · E02 – Login customer_a |
| E03 | `GET /api/profile/{id}/` | Coderr Profile GET · E03-01 – Customer reads own profile |
| E04 | `PATCH /api/profile/{id}/` | Coderr Profile PATCH · E04-01 – Update customer texts |
| E05 | `GET /api/profiles/business/` | Coderr Profile Lists · LIST – customer reads business profiles |
| E06 | `GET /api/profiles/customer/` | Coderr Profile Lists · LIST – customer reads customer profiles |
| E07 | `GET /api/offers/` | Coderr Offer LIST · LIST – Anonymous access and all seven fixtures |
| E08 | `POST /api/offers/` | Coderr Offer CREATE · E08 – Business creates three packages |
| E09 | `GET /api/offers/{id}/` | Coderr Offer DETAIL · E09 – Customer reads foreign offer A and captures package links |
| E10 | `PATCH /api/offers/{id}/` | Coderr Offer UPDATE DELETE · PATCH – Title only |
| E11 | `DELETE /api/offers/{id}/` | Coderr Offer UPDATE DELETE · DELETE – Owner deletes A |
| E12 | `GET /api/offerdetails/{id}/` | Coderr Offer DETAIL · E12 – Owner reads standard package |
| E13 | `GET /api/orders/` | Coderr Order LIST UPDATE DELETE · PREP – Capture existing staff participant list |
| E14 | `POST /api/orders/` | Coderr Order CREATE · CREATE – Customer buys basic |
| E15 | `PATCH /api/orders/{id}/` | Coderr Order LIST UPDATE DELETE · PATCH – Associated provider sets completed |
| E16 | `DELETE /api/orders/{id}/` | Coderr Order LIST UPDATE DELETE · DENIED – Deletion by ca |
| E17 | `GET /api/order-count/{id}/` | Coderr Order COUNT · EMPTY – a: order_count = 0 (customer) |
| E18 | `GET /api/completed-order-count/{id}/` | Coderr Order COUNT · EMPTY – a: completed_order_count = 0 (customer) |
| E19 | `GET /api/reviews/` | Coderr Review LIST · PREP – Remember existing review IDs |
| E20 | `POST /api/reviews/` | Coderr Review CREATE · CREATE – Customer c1 rates provider A with 1 without an order |
| E21 | `PATCH /api/reviews/{id}/` | Coderr Review UPDATE DELETE · PATCH – Rating only, lower bound |
| E22 | `DELETE /api/reviews/{id}/` | Coderr Review UPDATE DELETE · AUTH – Different reviewer DELETE |
| E23 | `GET /api/base-info/` | Coderr Base Info · PUBLIC – Anonymous opening snapshot |
