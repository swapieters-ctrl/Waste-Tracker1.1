from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import config

_scheduler = BackgroundScheduler(timezone="Europe/Amsterdam")


def stuur_wekelijks_rapport():
    import excel_export
    import email_sender

    vandaag = date.today()
    # Vorige week: maandag t/m zondag
    maandag = vandaag - timedelta(days=vandaag.weekday() + 7)
    zondag = maandag + timedelta(days=6)

    pad = excel_export.genereer_rapport(maandag, zondag)
    if config.MAIL_RECIPIENTS:
        email_sender.stuur_rapport(pad, maandag, zondag)


def start():
    _scheduler.add_job(
        stuur_wekelijks_rapport,
        trigger="cron",
        day_of_week=config.WEEKLY_REPORT_DAY,
        hour=config.WEEKLY_REPORT_HOUR,
        minute=config.WEEKLY_REPORT_MINUTE,
        id="wekelijks_rapport",
        replace_existing=True,
    )
    _scheduler.start()
