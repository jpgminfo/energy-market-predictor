from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper.jepx import run as run_jepx

scheduler = AsyncIOScheduler(timezone="Asia/Tokyo")

def setup_scheduler():
    # JEPX publishes previous day data around 10am JST
    scheduler.add_job(
        run_jepx,
        'cron',
        hour=14,
        minute=27,
        kwargs={"download": True},
        id="jepx_daily",
        replace_existing=True
    )
    scheduler.start()
    print("[Scheduler] JEPX daily job scheduled at 10:30 JST")

if __name__ == "__main__":
    # Manual trigger — run scraper immediately without downloading
    # Set download=True if you want Playwright to fetch the CSV
    print("Manually triggering JEPX scraper...")
    run_jepx(download=True)
    print("Done.")