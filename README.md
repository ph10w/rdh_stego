# RDH File Steganography
Versteckt beliebige Dateien in PNG-Bildern (Reversible Data Hiding) und stellt das Bild beim Extrahieren wieder her.
Enthält automatisch einen SHA-256-Hash, um die Integrität der eingebetteten Datei zu prüfen.

## Features
- Beliebige Dateien einbetten (PDF, ZIP, Bilder etc.)
- Originalbild rekonstruieren (außer Header-Pixel)
- Dateiname & SHA-256-Hash im Payload gespeichert
- Automatische Integritätsprüfung beim Extrahieren

## Voraussetzungen
- Python 3.8+
- Pillow, NumPy: `pip install pillow numpy`
- Verlustfreies Bildformat (PNG empfohlen)

## Einschränkungen
- Header-Pixel (~2000) verändert
- Nur verlustfreie Formate (PNG, BMP, TIFF)
- JPEG nicht geeignet
- Dateigröße ≤ verfügbare Kapazität
