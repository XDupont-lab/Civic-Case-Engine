# -*- coding: utf-8 -*-
"""
post_client.py
CivicHelper / CIVIC HELPER Tool
Hybride Fysieke Post-Vector voor het omzeilen van e-mailuitsluitingen (Awb art. 6:4).
Ondersteunt:
- Postbode.nu REST API (standaard en aangetekend via postbode-python / direct requests)
- Briefverzenden.nl integratiekader
- Dry-run & validatiemodus (pypdf pagina-telling & sha256 hashing)

Harde regel: Geen API-keys in bestanden. Wordt uitgelezen uit os.environ['POSTBODE_API_KEY'].
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import pypdf

class PostClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("POSTBODE_API_KEY", "")
        self.base_url = "https://api.postbode.nu/v1"

    def validate_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        pdf_path = Path(pdf_path)
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF niet gevonden: {pdf_path}")

        reader = pypdf.PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        file_size_kb = pdf_path.stat().st_size / 1024

        return {
            "path": str(pdf_path.resolve()),
            "pages": num_pages,
            "sha256": sha256,
            "size_kb": round(file_size_kb, 2),
            "is_single_page": (num_pages == 1)
        }

    def send_letter(
        self,
        pdf_path: Path,
        recipient_name: str,
        street_and_number: str,
        postal_code: str,
        city: str,
        country: str = "NL",
        registered: bool = False,
        color: bool = False,
        double_sided: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Verzendt een PDF per fysieke post via de Postbode API of simuleert in dry-run.
        """
        meta = self.validate_pdf(pdf_path)

        payload = {
            "recipient": {
                "name": recipient_name,
                "street": street_and_number,
                "postal_code": postal_code,
                "city": city,
                "country": country
            },
            "options": {
                "registered": registered,
                "color": color,
                "double_sided": double_sided
            },
            "document": meta
        }

        if dry_run or not self.api_key:
            print("[DRY-RUN / MOCK] PostClient: Geen actieve POSTBODE_API_KEY of expliciete dry-run geactiveerd.")
            print(f"  - Document: {meta['path']} ({meta['pages']} pag, SHA: {meta['sha256'][:12]}...)")
            print(f"  - Geadresseerde: {recipient_name}, {street_and_number}, {postal_code} {city}")
            print(f"  - Verzendwijze: {'Aangetekend' if registered else 'Standaard prior'} post")
            return {
                "success": True,
                "mode": "dry_run",
                "tracking_code": f"MOCK-POST-{meta['sha256'][:8].upper()}",
                "status": "simulated",
                "payload": payload
            }

        # Echte API-aanroep via requests / postbode API
        try:
            import urllib.request
            import urllib.error

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            req = urllib.request.Request(
                f"{self.base_url}/letters",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                return {
                    "success": True,
                    "mode": "live",
                    "letter_id": resp_data.get("id"),
                    "tracking_code": resp_data.get("tracking_code"),
                    "status": resp_data.get("status")
                }

        except Exception as e:
            print(f"[-] Fout bij live postverzending: {e}", file=sys.stderr)
            return {
                "success": False,
                "mode": "live_error",
                "error": str(e)
            }

if __name__ == "__main__":
    client = PostClient()
    print("PostClient operationeel in dry-run modus.")
