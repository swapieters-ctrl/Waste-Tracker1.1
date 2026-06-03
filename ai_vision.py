import base64
import re
import httpx
import anthropic
import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_SYSTEEM_PROMPT = """Je bent een assistent die productetiketten van voedingsmiddelen leest.
Geef ALTIJD een JSON-object terug met precies deze twee velden:
- "productnaam": de naam van het product op het etiket (string)
- "variant": één of meer van: normaal, vegetarisch, lactosevrij, glutenvrij
  (als er meerdere van toepassing zijn, geef ze als kommalijst; als er niets
   op het etiket staat, gebruik dan "normaal")

Voorbeeld:
{"productnaam": "Kipfilet", "variant": "glutenvrij"}
{"productnaam": "Groenteschotel", "variant": "vegetarisch,lactosevrij"}
{"productnaam": "Gehaktbal", "variant": "normaal"}

Geef ALLEEN het JSON-object terug, geen uitleg."""

_JSON_RE = re.compile(r'\{[^}]+\}', re.DOTALL)


def _download_als_base64(url: str, twilio_sid: str, twilio_token: str) -> tuple[str, str]:
    resp = httpx.get(url, auth=(twilio_sid, twilio_token), timeout=30)
    resp.raise_for_status()
    media_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
    return base64.standard_b64encode(resp.content).decode(), media_type


def lees_etiket(foto_url: str) -> dict:
    """Retourneert {"productnaam": str, "variant": str} op basis van de foto-URL."""
    b64, media_type = _download_als_base64(
        foto_url, config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN
    )

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=_SYSTEEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {"type": "text", "text": "Lees dit productetiket."},
                ],
            }
        ],
    )

    tekst = response.content[0].text.strip()
    match = _JSON_RE.search(tekst)
    if match:
        import json
        data = json.loads(match.group())
        return {
            "productnaam": data.get("productnaam", "Onbekend product"),
            "variant": data.get("variant", "normaal"),
        }

    return {"productnaam": "Onbekend product", "variant": "normaal"}


def parseer_correctie(tekst: str) -> dict:
    """Haal productnaam en variant uit een vrije-tekst correctie van de gebruiker."""
    VARIANTEN = ["vegetarisch", "lactosevrij", "glutenvrij"]
    gevonden = [v for v in VARIANTEN if v in tekst.lower()]
    variant = ",".join(gevonden) if gevonden else "normaal"

    naam = tekst.strip()
    for v in VARIANTEN:
        naam = re.sub(v, "", naam, flags=re.IGNORECASE).strip()
    naam = naam.strip(" ,")

    return {"productnaam": naam or tekst.strip(), "variant": variant}
