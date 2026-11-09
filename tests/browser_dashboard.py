"""Optional real-browser smoke test; separate from dependency-light unittest discovery."""

import argparse
from pathlib import Path
import tempfile
import threading

from playwright.sync_api import expect, sync_playwright

from security_ai.dashboard import Dashboard, DashboardServer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshots", type=Path, default=Path("artifacts/dashboard-preview"))
    args = parser.parse_args()
    args.screenshots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as output:
        dashboard = Dashboard(output)
        server = DashboardServer(0, dashboard)
        thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        )
        thread.start()
        try:
            with sync_playwright() as playwright:
                chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
                options = {"headless": True}
                if chrome.exists():
                    options["executable_path"] = str(chrome)
                browser = playwright.chromium.launch(**options)
                try:
                    context = browser.new_context(viewport={"width": 1440, "height": 1050})
                    # The page must not load remote scripts, fonts, or services.
                    context.route("**/*", lambda route: (
                        route.continue_() if route.request.url.startswith(server.origin + "/")
                        else route.abort()
                    ))
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(server.origin)
                    expect(page.get_by_role("heading", name="Security workspace", exact=True)).to_be_visible()
                    expect(page.locator("#roadmap-list .phase")).to_have_count(6)
                    expect(page.locator("#connection-state")).to_contain_text("AI not connected")
                    page.get_by_role("button", name="Run assessment", exact=True).click()
                    expect(page.locator("#run-status")).to_have_text("Completed", timeout=15000)
                    expect(page.locator("#history tr")).to_have_count(2)
                    expect(page.locator("#finding-list .finding")).to_have_count(1)
                    expect(page.locator("#evidence-panel details")).to_have_count(10)
                    page.get_by_role("tab", name="Recommended fix").click()
                    expect(page.locator("#fix-panel")).to_contain_text("ownership")
                    page.get_by_role("tab", name="Coverage & limits").click()
                    expect(page.locator("#coverage-panel")).to_contain_text("No AI model")
                    page.get_by_role("tab", name="Evidence", exact=True).click()
                    page.locator("#evidence-panel details").first.locator("summary").click()
                    with page.expect_download() as download:
                        page.get_by_role("link", name="Download report JSON").click()
                    download.value.save_as(args.screenshots / "downloaded-report.json")
                    page.screenshot(path=str(args.screenshots / "desktop.png"), full_page=True)
                    for width in (390, 320):
                        page.set_viewport_size({"width": width, "height": 844})
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= window.innerWidth"
                        ), "Page overflows at {}px".format(width)
                        expect(page.get_by_role("button", name="Run assessment", exact=True)).to_be_visible()
                    page.screenshot(path=str(args.screenshots / "mobile.png"), full_page=True)
                    page.set_viewport_size({"width": 1440, "height": 1050})
                    page.locator("#fixture").select_option("vulnerable")
                    page.locator("#request-limit").fill("1")
                    page.get_by_role("button", name="Run assessment", exact=True).click()
                    expect(page.locator("#run-status")).to_have_text("Partial", timeout=10000)
                    expect(page.locator("#report-outcome")).to_contain_text("Assessment incomplete")
                    page.get_by_role("tab", name="Coverage & limits").click()
                    expect(page.locator("#coverage-panel")).to_contain_text("REQUEST_BUDGET_EXHAUSTED")
                    page.locator("#fixture").select_option("both")
                    page.locator("#request-limit").fill("30")
                    page.get_by_role("button", name="Run assessment", exact=True).click()
                    page.get_by_role("button", name="Stop run", exact=True).click()
                    expect(page.locator("#run-status")).to_have_text("Cancelled", timeout=10000)
                    assert not errors, errors
                    print("Browser checks passed: real comparison, evidence/fix/coverage tabs, "
                          "JSON download, 390/320px layouts, partial result, cancellation, "
                          "and no JavaScript exceptions.")
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            dashboard.close()


if __name__ == "__main__":
    main()
