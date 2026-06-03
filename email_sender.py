import smtplib
import os
from email.message import EmailMessage
from datetime import date
import config


def stuur_rapport(bestand_pad: str, van: date, tot: date):
    week_nr = van.isocalendar().week
    jaar = van.year

    msg = EmailMessage()
    msg["Subject"] = (
        f"Voedselverspilling rapport week {week_nr:02d} "
        f"({van.strftime('%d %b')} – {tot.strftime('%d %b %Y')})"
    )
    msg["From"] = config.MAIL_FROM
    msg["To"] = ", ".join(config.MAIL_RECIPIENTS)

    totaal_registraties = _tel_registraties(van, tot)
    msg.set_content(
        f"Beste,\n\n"
        f"Bijgevoegd het voedselverspillingsrapport voor week {week_nr:02d} "
        f"({van.strftime('%d-%m-%Y')} t/m {tot.strftime('%d-%m-%Y')}).\n\n"
        f"Totaal aantal registraties deze week: {totaal_registraties}\n\n"
        f"Het Excel-bestand bevat:\n"
        f"  • Tabblad 1 – Alle registraties (datum, tijdstip, product, variant, kilo's)\n"
        f"  • Tabblad 2 – Wekelijks totaal per product\n\n"
        f"Met vriendelijke groet,\n"
        f"Voedselverspilling Tracker"
    )

    with open(bestand_pad, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(bestand_pad),
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(config.MAIL_FROM, config.MAIL_PASSWORD)
        smtp.send_message(msg)


def _tel_registraties(van: date, tot: date) -> int:
    import database
    return len(database.haal_registraties_op(van, tot))
