from flask import Flask, request, jsonify
import database
import whatsapp
import excel_export
import email_sender
import scheduler

app = Flask(__name__)
database.init_db()
scheduler.start()


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    telefoon = request.form.get("From", "")
    tekst = request.form.get("Body", "").strip()
    media_url = request.form.get("MediaUrl0")

    whatsapp.verwerk_bericht(telefoon, tekst, media_url)
    return "", 204


@app.route("/export", methods=["GET"])
def export_week():
    """Handmatig exporteren voor testen. Geeft het Excel-bestand terug als download."""
    from datetime import date, timedelta
    vandaag = date.today()
    maandag = vandaag - timedelta(days=vandaag.weekday())
    zondag = maandag + timedelta(days=6)

    pad = excel_export.genereer_rapport(maandag, zondag)
    from flask import send_file
    return send_file(pad, as_attachment=True)


@app.route("/send-weekly", methods=["POST"])
def send_weekly():
    """Handmatig sturen voor testen."""
    scheduler.stuur_wekelijks_rapport()
    return jsonify({"status": "verstuurd"})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
