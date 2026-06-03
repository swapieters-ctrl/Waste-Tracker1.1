"""
Verwerkt inkomende WhatsApp-berichten via een eenvoudige state machine.

Fases per telefoonnummer:
  idle              → wacht op een foto
  wacht_bevestiging → foto ontvangen, AI-herkenning klaar, wacht op ja/nee
  wacht_correctie   → gebruiker zei "nee", wacht op gecorrigeerde naam/variant
  wacht_kilo        → naam bevestigd, wacht op het gewicht in kilo's
"""

import re
from twilio.rest import Client
import config
import database
import ai_vision

_twilio = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def stuur(naar: str, bericht: str):
    _twilio.messages.create(
        from_=config.TWILIO_WHATSAPP_FROM,
        to=naar,
        body=bericht,
    )


def _variant_label(variant: str) -> str:
    if variant and variant != "normaal":
        return f" ({variant})"
    return ""


def verwerk_bericht(telefoon: str, tekst: str, media_url: str | None):
    status = database.haal_status_op(telefoon)
    fase = status["fase"]

    # ── Foto ontvangen (altijd verwerken, ongeacht fase) ──────────────────────
    if media_url:
        stuur(telefoon, "Foto ontvangen, ik lees het etiket... even geduld.")
        try:
            resultaat = ai_vision.lees_etiket(media_url)
        except Exception:
            stuur(telefoon, "Fout bij het lezen van het etiket. Probeer opnieuw.")
            database.reset_status(telefoon)
            return

        naam = resultaat["productnaam"]
        variant = resultaat["variant"]
        label = _variant_label(variant)

        database.sla_status_op(
            telefoon,
            fase="wacht_bevestiging",
            productnaam_ai=naam,
            variant_ai=variant,
            foto_url=media_url,
        )
        stuur(telefoon, f"Heb ik herkend: *{naam}*{label}.\nKlopt dit? (ja/nee)")
        return

    tekst_lower = tekst.strip().lower()

    # ── wacht_bevestiging ─────────────────────────────────────────────────────
    if fase == "wacht_bevestiging":
        if tekst_lower in ("ja", "j", "yes", "y", "ok", "oke", "oké", "correct", "klopt"):
            database.sla_status_op(
                telefoon,
                fase="wacht_kilo",
                productnaam_ai=status["productnaam_ai"],
                variant_ai=status["variant_ai"],
                foto_url=status["foto_url"],
            )
            stuur(telefoon, "Hoeveel kilo's?")
        elif tekst_lower in ("nee", "n", "no", "fout", "niet"):
            database.sla_status_op(
                telefoon,
                fase="wacht_correctie",
                productnaam_ai=status["productnaam_ai"],
                variant_ai=status["variant_ai"],
                foto_url=status["foto_url"],
            )
            stuur(
                telefoon,
                "Wat is de juiste productnaam en variant?\n"
                "(bijv: _Kipfilet marinade glutenvrij_)",
            )
        else:
            stuur(telefoon, "Antwoord met *ja* of *nee*.")
        return

    # ── wacht_correctie ───────────────────────────────────────────────────────
    if fase == "wacht_correctie":
        gecorrigeerd = ai_vision.parseer_correctie(tekst)
        naam = gecorrigeerd["productnaam"]
        variant = gecorrigeerd["variant"]
        label = _variant_label(variant)

        database.sla_status_op(
            telefoon,
            fase="wacht_kilo",
            productnaam_ai=naam,
            variant_ai=variant,
            foto_url=status["foto_url"],
        )
        stuur(telefoon, f"Begrepen: *{naam}*{label}.\nHoeveel kilo's?")
        return

    # ── wacht_kilo ────────────────────────────────────────────────────────────
    if fase == "wacht_kilo":
        kilo_match = re.search(r"\d+([.,]\d+)?", tekst)
        if not kilo_match:
            stuur(telefoon, "Voer een geldig gewicht in (bijv: 3.5 of 2,5).")
            return

        kilo = float(kilo_match.group().replace(",", "."))
        naam = status["productnaam_ai"]
        variant = status["variant_ai"]
        label = _variant_label(variant)

        database.sla_registratie_op(telefoon, naam, variant, kilo)
        database.reset_status(telefoon)

        from datetime import datetime
        datum_str = datetime.now().strftime("%d-%m-%Y om %H:%M")
        stuur(
            telefoon,
            f"✅ Geregistreerd:\n*{naam}*{label} — {kilo} kg\n_{datum_str}_",
        )
        return

    # ── idle: geen foto, onverwacht bericht ───────────────────────────────────
    stuur(
        telefoon,
        "Stuur een foto van het productetiket om een registratie te starten.",
    )
