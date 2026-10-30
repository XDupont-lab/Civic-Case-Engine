"""Vervang kale identificatiecodes door plaatshouders, en zet ze lokaal terug.

Burgerservicenummer, bankrekening en huisadres gaan niet naar een extern model.
Diagnoses, uitslagen, datums en briefteksten blijven staan.
"""

import re

_BSN = re.compile(
    r"(?i)(?:\bburgerservicenummer\b|\bbsn\b)\s*(?:is\b|[:\-])?\s*(\d{8,9}|\d{3}[\.\s]?\d{3}[\.\s]?\d{3})"
    r"|(?<!\d)(\d{3}[\.\s]\d{3}[\.\s]\d{3})(?!\d)"
)
_IBAN = re.compile(
    r"\b[A-Z]{2}\d{2}\s?[A-Z]{4}\s?(?:\d\s?){8,22}\b",
    re.IGNORECASE,
)
# Straat + huisnummer + postcode (+ woonplaats), of losse postcode (4 cijfers + 2 HOOFDLETTERS, geen jaartal + medische afkorting zoals '2016 IC')
_MED_ABBR = r"(?:IC|SE|CT|MR|OD|OS|MG|ML|IU|GB|MB|KG|CM|MM|HR|RR|HB|AL|AS|CR|PR|IV|PO|SC|IM)"
_ADRES = re.compile(
    r"(?:\b[A-Z][a-zA-Zëïöüéè\-]+(?:straat|laan|weg|hof|plein|gracht|singel|kade|dijk|pad|steeg|heerd|diep|oord|ring|markt|kamp|veld|baan|drift|wijk)\s+\d+[a-zA-Z\-]?(?:[,\s]+[1-9]\d{3}\s?[A-Z]{2}(?:\s+[A-Z][a-zA-Zëïöüéè\-]+)?)?)"
    r"|(?:\b[A-Z][a-zA-Zëïöüéè\-]+\s+\d+[a-zA-Z\-]?,\s*[1-9]\d{3}\s?[A-Z]{2}(?:\s+[A-Z][a-zA-Zëïöüéè\-]+)?)"
    r"|(?:\b(?!(?:19\d\d|20[0-3]\d)\s+" + _MED_ABBR + r"\b)[1-9]\d{3}\s?[A-Z]{2}\b(?:\s+[A-Z][a-zA-Zëïöüéè\-]+)?)"
)


class Vault:
    def __init__(self):
        self._map = {}
        self._n = {"BSN": 0, "IBAN": 0, "ADRES": 0}

    def put(self, kind, value):
        for token, original in self._map.items():
            if original == value:
                return token
        self._n[kind] += 1
        token = f"[{kind}-{self._n[kind]}]"
        self._map[token] = value
        return token

    def restore(self, text):
        if not text:
            return text
        for token, original in self._map.items():
            text = text.replace(token, original)
        return text


def mask(text, vault=None):
    """Geeft (gemaskeerde tekst, kluis) terug."""
    if text is None:
        return text, vault or Vault()
    vault = vault or Vault()

    def bsn_sub(match):
        raw = match.group(1) or match.group(2)
        return match.group(0).replace(raw, vault.put("BSN", raw))

    text = _BSN.sub(bsn_sub, text)

    def iban_sub(match):
        raw = match.group(0)
        return vault.put("IBAN", raw)

    text = _IBAN.sub(iban_sub, text)

    def adres_sub(match):
        raw = match.group(0)
        return vault.put("ADRES", raw)

    text = _ADRES.sub(adres_sub, text)
    return text, vault


def restore(text, vault):
    if vault is None:
        return text
    return vault.restore(text)
