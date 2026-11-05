# Coderr – Order counters

## Lokal ausführen

1. Im Backend-Terminal `python manage.py runserver` starten und laufen lassen.
2. Die Collection `Coderr_Order_COUNT.postman_collection.json` und das Environment
   `Coderr_Order_Count_Local.postman_environment.json` in Postman importieren.
3. Environment **Coderr Order Count Local** auswählen.
4. Collection **Coderr Order COUNT** über **Run collection** vollständig ausführen.
5. Eine Iteration, alle Requests aktiviert, ursprüngliche Reihenfolge beibehalten.

Erwartet: **82 Requests, 212 bestandene Assertions, keine Fehler**.
Keine manuell einzutragenden Tokens, Passwörter oder Upload-Dateien erforderlich.
`base_url` enthält `/api`, aber keinen abschließenden Slash.

## Abdeckung

- GET `/api/order-count/{business_user_id}/`: ausschließlich `in_progress`.
- GET `/api/completed-order-count/{business_user_id}/`: ausschließlich `completed`.
- Exakte Antwortschlüssel, ganzzahlige nichtnegative Zahlen, leere Anbieter liefern 0.
- Zwei Anbieter mit unterschiedlichen Anzahlen und Bestellungen von zwei Kunden.
- Angemeldete Kunden, eigener Anbieter und fremder Anbieter dürfen Zähler lesen.
- `cancelled` wird in keinem Zähler mitgezählt.
- Statuswechsel completed → cancelled → in_progress ändern die Zähler korrekt.
- Ungültige und verbotene PATCH-Anfragen verändern die Zähler nicht.
- Fehlender/ungültiger Token: 401; Kunden-ID/unbekannter Anbieter: 404.
- Wiederholte Zählerabfragen verändern Bestellungen oder Zeitstempel nicht.
- Löschen des ursprünglichen Angebots erhält die Bestellungen und ihre Zähler.
- Gültige Abfragen funktionieren nach abgelehnten Anfragen weiterhin.

## Testdaten und Wiederholung

Pro vollständigem Lauf werden fünf eindeutig benannte Benutzer, zwei Angebote und
sechs Bestellungen erzeugt. Die beiden Angebote werden am Ende gelöscht.
**Fünf Benutzer und sechs Bestellungen bleiben in der lokalen Datenbank.**
Es werden ausschließlich Angebote dieses Laufs gelöscht. Vorhandene Daten werden
nicht geändert. Die Bestellungen bleiben bestehen, weil ihre Löschung einen
Staff-Account benötigt und die Collection ohne Zugangsdaten ausführbar sein soll.

Für einen neuen Lauf die gesamte Collection von vorne starten. Einzelne Requests
setzen die dynamischen IDs und Tokens aus den vorherigen Vorbereitungsschritten voraus.
Die unbekannte Anbieter-ID 2147483647 muss in der lokalen Testdatenbank unbenutzt sein.
Ein Vorbereitungsschritt mit ungültiger Antwort beendet die weitere Ausführung.

## Fehler untersuchen

Im Runner den ersten fehlgeschlagenen Request öffnen und dessen tatsächlichen
Statuscode sowie Response-Body prüfen. Folgefehler zunächst zurückstellen.
401: ausgewähltes Environment und Vorbereitungsschritte prüfen.
404 bei gültigen Anbieter-IDs: Route und laufenden Backend-Stand prüfen.
Keine Verbindung: Django-Server und `base_url` prüfen.

## Prüfgrenze

Collection-Struktur und Testskripte wurden mit kontrollierten Antworten geprüft.
Der tatsächliche HTTP-Lauf erfolgt gegen dein lokales Django-Backend in Postman.
