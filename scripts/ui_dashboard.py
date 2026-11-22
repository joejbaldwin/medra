"""Interaction check of the dashboard layout (build step 6).

Drives the real dashboard in a browser and checks the window manager, the
«Añadir visualización» picker and the chat: search and filters, Escape and
focus return, the Tab trap, adding and removing windows, moving them by drag
and by arrow keys, collapsing and expanding the chat, pages, highlighting
across windows, and the paste source. Uses the recorded traces and pasted
text only, so it spends no API credit.

Needs the backend and the Vite dev server running (see README).

    python scripts/ui_dashboard.py --channel chromium-headless-shell
"""

from __future__ import annotations

import argparse

from playwright.sync_api import sync_playwright

ACTIVE = ".page:not([hidden])"  # the dashboard page on screen
fails: list[str] = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def choose_source(page, value):
    """Pick a source in the «Fuente» menu (a custom listbox; the <select> behind it is hidden)."""
    page.click("#source-button")
    page.click(f"#source-menu li[data-value='{value}']")


def cells(page):
    return page.eval_on_selector_all(
        f"{ACTIVE} > *",
        "els => els.map(e => (e.dataset.win || 'slot') + (e.classList.contains('covered') ? '~' : '') + ':' + e.dataset.cells)",
    )


parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:5173/")
parser.add_argument("--channel", default="chromium-headless-shell")
args = parser.parse_args()
URL = args.url

with sync_playwright() as p:
    b = p.chromium.launch(channel=args.channel)
    ctx = b.new_context(viewport={"width": 1600, "height": 1000})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#source[data-loaded]", state="attached")
    page.wait_for_selector("#sample option[value='login-es']", state="attached")

    # Defaults: chat open, every other slot empty, page 2 blank, light theme, the odd-sum trace.
    check(cells(page) == ["slot:0", "slot:1", "chat:2,3"], f"initial page 1 layout {cells(page)}")
    check(page.get_attribute("html", "data-theme") == "light", "light theme by default")
    check(page.input_value("#sample") == "odd-sum-en", f"default trace {page.input_value('#sample')}")
    check(page.input_value("#composer-input").startswith("What is the sum"), "trace prompt loaded into the composer")
    check(page.get_attribute("#composer-input", "readonly") is not None, "recorded prompt is read-only")
    page.select_option("#sample", "login-es")
    check(page.input_value("#composer-input") == "Crea una página de login.", "changing the trace changes the prompt")
    # The rest of the check starts from the timeline in the lower-left slot.
    page.click(f"{ACTIVE} .slot-add >> nth=1")
    page.click(".viz-card[data-kind='timeline'] .add-btn")
    check(cells(page) == ["slot:0", "timeline:1", "chat:2,3"], f"timeline added below the empty slot {cells(page)}")

    # Picker: open, search, filters, escape, focus return.
    page.click(f"{ACTIVE} .slot-add")
    page.wait_for_selector("#picker[open]")
    check(page.evaluate("document.activeElement.type") == "search", "picker focuses its search field")
    page.fill("#picker input", "linea")
    vis = lambda: page.eval_on_selector_all(".viz-card:not([hidden])", "els => els.map(e => e.dataset.kind)")
    check(vis() == ["timeline"], f"search 'linea' -> {vis()}")
    page.fill("#picker input", "")
    page.click(".chips button[data-cat='Pasos']")
    check(vis() == ["steps"], f"filter Pasos -> {vis()}")
    page.fill("#picker input", "zzz")
    check(vis() == [] and page.is_visible(".picker-empty"), "no match shows the empty message")
    page.fill("#picker input", "")
    page.click(".chips button[data-cat='']")
    check(vis() == ["map", "timeline", "steps"], "Todas shows the three cards")
    for _ in range(12):
        page.keyboard.press("Tab")
    inside = page.evaluate("document.getElementById('picker').contains(document.activeElement)")
    check(inside, "Tab stays inside the picker")
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check(not page.is_visible("#picker"), "Escape closes the picker")
    check(page.evaluate("document.activeElement.classList.contains('slot-add')"), "focus returns to the slot's + button")

    # Play the trace.
    page.select_option("#speed", "75")
    page.click("#send")
    page.wait_for_function("document.getElementById('status').dataset.state === 'live'", timeout=30000)
    check(page.text_content("#status").lower() == "reproduciendo", f"replay labelled as such: {page.text_content('#status')}")
    check("traza grabada" in page.inner_text("#mode-badge"), f"badge {page.inner_text('#mode-badge')}")
    page.wait_for_function("document.getElementById('status').dataset.state === 'done'", timeout=60000)
    page.wait_for_timeout(800)
    check(page.inner_text("#prompt") == "Crea una página de login.", "user message shows the trace prompt")

    # Decluttered chat and views: no legend lines, no status strip, a smaller send button.
    check(page.locator(".panel-sub, #chat-status, #ticker-now").count() == 0, "no view subtitles or status strip")
    check(not page.is_visible(f"{ACTIVE} .step-detail") and not page.is_visible(f"{ACTIVE} .map-info"), "no hint lines while nothing is selected")
    check("Densidad de menciones" in (page.get_attribute(f"{ACTIVE} [data-win='timeline'] .win-title", "title") or ""), "the view hint lives in the title tooltip")
    box = page.locator("#send").bounding_box()
    check(box and round(box["width"]) == 38, f"send button is 38 px ({box and box['width']})")
    check("en directo" not in page.inner_text("#mode-badge"), "replay badge does not say en directo")

    # «Estadísticas»: a popup from the header with the trace's mining figures.
    page.click("#stats-open")
    check(page.is_visible("#stats-dialog"), "stats popup opens from the header")
    tiles = page.locator("#stats-body .tile").count()
    words = page.inner_text("#stats-body .tile:first-child .tile-value").replace(".", "").replace("\u202f", "").strip()
    check(tiles == 8 and words.isdigit() and int(words) > 50, f"stats popup shows {tiles} figures, {words} words")
    check(page.locator("#stats-body .bar-row").count() >= 3, "stats popup shows bars for concepts and steps")
    check("terminado" in page.inner_text("#status").lower(), f"popup shows the session status: {page.inner_text('#status')}")
    check(page.inner_text("#stats-session") != "Ninguna traza todavía.", f"popup names the trace: {page.inner_text('#stats-session')}")
    page.keyboard.press("Escape")
    check(not page.is_visible("#stats-dialog"), "Escape closes the stats popup")
    check(page.evaluate("document.activeElement.id") == "stats-open", "focus returns to the Estadísticas button")

    # «Fuente» menu: a listbox with an icon per source, by keyboard.
    page.focus("#source-button")
    page.keyboard.press("ArrowDown")
    check(page.is_visible("#source-menu .src-list"), "ArrowDown opens the source menu")
    check(page.locator("#source-menu li .src-icon").count() == page.locator("#source-menu li").count(), "every source has an icon")
    ds = page.locator("#source-menu li[data-value='deepseek']")
    if ds.count():
        check(ds.locator("path[fill='#4D6BFE']").count() == 1, f"DeepSeek option shows the DeepSeek logo ({ds.inner_text()})")
    page.keyboard.press("Escape")
    check(not page.is_visible("#source-menu .src-list") and page.evaluate("document.activeElement.id") == "source-button", "Escape closes the menu, focus back on its button")
    check(page.is_visible("#answer-block"), "answer shown")

    # Add the map mid-session: populated at once.
    page.click(f"{ACTIVE} .slot-add")
    page.click(".viz-card[data-kind='map'] .add-btn")
    page.wait_for_timeout(300)
    n = page.eval_on_selector_all(f"{ACTIVE} [data-win='map'] g.node", "els => els.length")
    check(n == 16, f"new map window filled from the session: {n} bubbles")
    check(page.evaluate("document.activeElement.classList.contains('grip')"), "focus moves to the new window's handle")

    # Highlight both ways.
    page.click(f"{ACTIVE} [data-win='map'] g.node[data-id='login']")
    hl = page.eval_on_selector_all(".m.hl", "els => els.length")
    check(hl > 0, f"bubble click underlines {hl} mentions")
    page.click(f"{ACTIVE} [data-win='map'] g.node[data-id='login']")
    page.click(f"{ACTIVE} .legend button >> nth=0")
    sel = page.eval_on_selector_all("#stream .para.sel", "els => els.length")
    check(sel > 0, f"topic click highlights {sel} paragraphs")
    page.click(f"{ACTIVE} .legend button >> nth=0")

    # Remove and re-add the timeline: data intact.
    page.click(f"{ACTIVE} [data-win='timeline'] .win-close")
    check(cells(page) == ["map:0", "slot:1", "chat:2,3"], f"timeline removed {cells(page)}")
    check(page.evaluate("document.activeElement.classList.contains('slot-add')"), "focus goes to the freed slot")
    page.click(f"{ACTIVE} .slot-add")
    page.click(".viz-card[data-kind='timeline'] .add-btn")
    legend = page.eval_on_selector_all(f"{ACTIVE} .legend button", "els => els.length")
    curves = page.eval_on_selector_all(f"{ACTIVE} g.c-topic", "els => els.length")
    check(legend == 2 and curves == 2, f"re-added timeline has {curves} curves, {legend} legend entries")

    # Keyboard move: map right, onto the expanded chat (column swap).
    page.focus(f"{ACTIVE} [data-win='map'] .grip")
    page.keyboard.press("ArrowRight")
    check(cells(page) == ["chat:0,1", "map:2", "timeline:3"], f"ArrowRight on map {cells(page)}")
    check(page.evaluate("document.activeElement.closest('[data-win]')?.dataset.win") == "map", "focus stays on the moved handle")
    # The announcer is updated on the next animation frame (so repeats are read out again).
    page.wait_for_function("document.getElementById('announcer').textContent !== ''", timeout=2000)
    check(page.inner_text("#announcer").startswith("Mapa de conceptos movido"), f"announced: {page.inner_text('#announcer')}")
    page.keyboard.press("ArrowLeft")
    check(cells(page) == ["map:0", "timeline:1", "chat:2,3"], f"ArrowLeft back {cells(page)}")

    # Pointer drag: timeline onto the chat's upper half.
    grip = page.locator(f"{ACTIVE} [data-win='timeline'] .grip").bounding_box()
    chat = page.locator("#chat-win").bounding_box()
    page.mouse.move(grip["x"] + 10, grip["y"] + 10)
    page.mouse.down()
    page.mouse.move(grip["x"] + 60, grip["y"] - 20, steps=4)
    page.mouse.move(chat["x"] + 200, chat["y"] + 100, steps=8)
    check(page.locator("#chat-win.drop-target").count() == 1, "drop target highlighted while dragging")
    page.mouse.up()
    check(cells(page) == ["chat:0,1", "timeline:2", "map:3"], f"drag timeline onto chat {cells(page)}")
    scroll_top = page.evaluate("document.getElementById('chat-scroll').scrollTop")
    # Drag the chat back to the right column.
    grip = page.locator("#chat-win .grip").bounding_box()
    tl = page.locator(f"{ACTIVE} [data-win='timeline']").bounding_box()
    page.mouse.move(grip["x"] + 10, grip["y"] + 10)
    page.mouse.down()
    page.mouse.move(tl["x"] + 100, tl["y"] + 100, steps=10)
    page.mouse.up()
    check(cells(page) == ["timeline:0", "map:1", "chat:2,3"], f"drag chat back {cells(page)}")
    check(abs(page.evaluate("document.getElementById('chat-scroll').scrollTop") - scroll_top) < 2, "chat keeps its scroll position across moves")
    # Escape cancels a drag.
    grip = page.locator(f"{ACTIVE} [data-win='map'] .grip").bounding_box()
    page.mouse.move(grip["x"] + 10, grip["y"] + 10)
    page.mouse.down()
    page.mouse.move(chat["x"] + 100, chat["y"] + 100, steps=8)
    page.keyboard.press("Escape")
    page.mouse.up()
    check(cells(page) == ["timeline:0", "map:1", "chat:2,3"], "Escape cancels a drag")

    # Collapse / expand the chat.
    page.click("#chat-toggle")
    check(cells(page) == ["timeline:0", "map:1", "slot:2", "chat:3"], f"collapsed chat {cells(page)}")
    check(page.get_attribute("#chat-toggle", "aria-expanded") == "false", "toggle reports collapsed")
    check(page.locator("#stream .para").count() >= 4, "collapsed chat keeps its content")
    page.click(f"{ACTIVE} .slot-add")
    page.click(".viz-card[data-kind='steps'] .add-btn")
    page.click("#chat-toggle")
    check(cells(page) == ["timeline:0", "map:1", "steps:2", "chat:3"], "expand refused when the page is full")
    check(page.is_visible("#toast"), f"toast: {page.inner_text('#toast')}")
    page.click(f"{ACTIVE} [data-win='map'] .win-close")
    page.click("#chat-toggle")
    check(cells(page) == ["timeline:0", "steps:1", "chat:2,3"], f"expand moves the covered window {cells(page)}")

    # Steps panel selection highlights a paragraph.
    page.click(f"{ACTIVE} g.s-node >> nth=2")
    lit = page.eval_on_selector_all("#stream .para.sel", "els => els.map(e => e.dataset.seg)")
    check(len(lit) == 1, f"step click highlights paragraph {lit}")
    check("Corrección" in page.inner_text(f"{ACTIVE} .step-detail"), "step detail shows the step type")
    page.click(f"{ACTIVE} g.s-node >> nth=2")

    # Pages.
    page.click("#page-tab-1")
    check(cells(page) == ["slot:0", "slot:1", "slot:2", "slot:3"], f"page 2 starts blank {cells(page)}")
    for kind in ("map", "timeline", "steps"):  # each fills the first free slot
        page.click(f"{ACTIVE} .slot-add >> nth=0")
        page.click(f".viz-card[data-kind='{kind}'] .add-btn")
    page.wait_for_timeout(300)
    check(cells(page) == ["map:0", "timeline:1", "steps:2", "slot:3"], f"page 2 {cells(page)}")
    n = page.eval_on_selector_all(f"{ACTIVE} g.node", "els => els.length")
    w = page.evaluate(f"document.querySelector('{ACTIVE} .chart-wrap svg').getAttribute('viewBox')")
    steps_n = page.eval_on_selector_all(f"{ACTIVE} g.s-node", "els => els.length")
    check(n == 16 and steps_n == 4, f"page 2 views populated: {n} bubbles, {steps_n} steps, chart viewBox {w}")
    page.click(f"{ACTIVE} g.node[data-id='contraseña']")
    page.click("#page-tab-0")
    hl = page.eval_on_selector_all(".m.hl", "els => els.length")
    check(hl > 0, f"selection made on page 2 shows in the chat on page 1 ({hl} mentions)")
    page.click("#pager-add")
    check(page.get_attribute("#page-tab-2", "aria-selected") == "true", "+ creates and selects page 3")
    check(cells(page) == ["slot:0", "slot:1", "slot:2", "slot:3"], f"page 3 {cells(page)}")
    check(page.locator("#chat-win").count() == 1, "still one chat window")

    # Two-cell windows, on the empty page 3: map top-left, timeline bottom-right.
    page.click(f"{ACTIVE} .slot-add >> nth=0")
    page.click(".viz-card[data-kind='map'] .add-btn")
    page.click(f"{ACTIVE} .slot-add >> nth=2")
    page.click(".viz-card[data-kind='timeline'] .add-btn")
    check(cells(page) == ["map:0", "slot:1", "slot:2", "timeline:3"], f"page 3 filled {cells(page)}")
    # Enlarging (row, column, whole page) is drawn over the page; what it covers
    # is hidden ("~") and comes back on restore.
    btn = lambda kind, mode: f"{ACTIVE} [data-win='{kind}'] [data-expand='{mode}']"
    page.click(btn("map", "row"))
    check(cells(page) == ["map:0,2", "slot:1", "timeline:3"], f"map fills its row {cells(page)}")
    check(page.get_attribute(btn("map", "row"), "aria-pressed") == "true" and page.get_attribute(btn("map", "row"), "aria-label").startswith("Restaurar"), "row button now restores")
    page.click(btn("map", "column"))  # switch straight to the column
    check(cells(page) == ["map:0,1", "slot:2", "timeline:3"], f"map fills its column {cells(page)}")
    page.wait_for_timeout(300)
    h_map = page.locator(f"{ACTIVE} [data-win='map']").bounding_box()["height"]
    h_tl = page.locator(f"{ACTIVE} [data-win='timeline']").bounding_box()["height"]
    check(h_map > 1.9 * h_tl, f"column window is twice as tall ({h_map:.0f} vs {h_tl:.0f} px)")
    page.click(btn("map", "full"))
    check(cells(page) == ["map:0,1,2,3", "timeline~:3"], f"map fills the page over the timeline {cells(page)}")
    check(not page.is_visible(f"{ACTIVE} [data-win='timeline'] .win-title"), "covered timeline hidden")
    page.keyboard.press("Escape")
    check(cells(page) == ["map:0", "slot:1", "slot:2", "timeline:3"], f"Escape restores the page {cells(page)}")
    check(page.evaluate("document.activeElement.dataset.expand") == "full", "focus back on the full-page button")
    page.click(btn("map", "row"))
    page.focus(f"{ACTIVE} [data-win='map'] .grip")
    page.keyboard.press("ArrowDown")
    check(cells(page) == ["slot:0", "map:1,3", "timeline:2"], f"ArrowDown moves the enlarged map as a row {cells(page)}")
    page.click(btn("timeline", "column"))  # covers the map: allowed now, the map goes back to its cell
    check(cells(page) == ["slot:0", "map:1", "timeline:2,3"], f"timeline fills its column over the map {cells(page)}")
    check(not page.is_visible("#toast"), "no refusal message")
    page.click(btn("timeline", "column"))
    check(cells(page) == ["slot:0", "map:1", "timeline:2", "slot:3"], f"timeline restored {cells(page)}")
    page.click("#page-tab-0")
    # Over the chat: the whole page hides it, a row leaves it its lower half.
    scroll_top = page.evaluate("document.getElementById('chat-scroll').scrollTop")
    page.click(btn("timeline", "full"))
    check(cells(page) == ["timeline:0,1,2,3", "steps~:1", "chat~:2,3"] and not page.is_visible("#chat-title"), f"full page covers the chat {cells(page)}")
    page.click(btn("timeline", "full"))
    check(cells(page) == ["timeline:0", "steps:1", "chat:2,3"] and page.is_visible("#chat-title"), f"chat back after restoring {cells(page)}")
    check(abs(page.evaluate("document.getElementById('chat-scroll').scrollTop") - scroll_top) < 2, "chat keeps its scroll position under an enlarged window")
    page.click(btn("timeline", "row"))
    check(cells(page) == ["timeline:0,2", "steps:1", "chat:3"] and "collapsed" in page.get_attribute("#chat-win", "class"), f"row leaves the chat its lower half {cells(page)}")
    page.click("#chat-toggle")
    check(cells(page) == ["timeline:0", "steps:1", "chat:2,3"], f"chat toggle restores the page {cells(page)}")
    check(page.is_visible("#chat-win") and page.locator("#stream .para").count() >= 4, "session intact after page switching")
    check(not page.is_visible("#chat-progress"), "no progress line once the text has arrived")

    # Paste mode.
    choose_source(page, "paste")
    check(page.get_attribute("#composer-input", "readonly") is None, "paste box editable")
    check(not page.is_visible("#sample-field"), "Traza menu hidden for paste")
    page.fill("#composer-input", "Okay, let me think. The cache must be invalidated. Wait, the cache key includes the user. So the cache key changes and the cache is fine.\n\nAlternatively, the cache could expire. The cache expiry is simpler.")
    page.keyboard.press("Control+Enter")
    page.wait_for_function("document.getElementById('status').dataset.state === 'done'", timeout=60000)
    check(page.inner_text("#prompt").startswith("Texto pegado"), f"paste user message: {page.inner_text('#prompt')}")
    check("texto pegado" in page.inner_text("#mode-badge"), f"paste badge {page.inner_text('#mode-badge')}")
    choose_source(page, "replay")
    choose_source(page, "paste")
    check(page.input_value("#composer-input").startswith("Okay, let me think"), "paste draft kept when switching sources")
    check(page.locator("#source-note").count() == 0, "no source note under the composer")

    # Stop: the send button becomes a square while a session runs, and aborts it.
    page.select_option("#speed", "8")
    page.click("#send")
    page.wait_for_function("document.getElementById('status').dataset.state === 'live' && document.getElementById('stream').textContent.length > 20", timeout=30000)
    check(page.get_attribute("#send", "aria-label") == "Detener" and "stop" in page.get_attribute("#send", "class"), "send button turns into stop while pasting plays")
    page.click("#send")
    shown = page.evaluate("document.getElementById('stream').textContent.length")
    page.wait_for_timeout(1500)
    check(page.evaluate("document.getElementById('stream').textContent.length") == shown, "stopped paste receives no more text")
    check(page.get_attribute("#status", "data-state") == "stopped" and page.is_visible("#chat-notice"), f"stopped status and notice: {page.text_content('#status')}")
    check(page.get_attribute("#send", "aria-label") == "Enviar", "button is send again after stopping")
    choose_source(page, "replay")
    page.click("#send")
    page.wait_for_function("document.getElementById('status').dataset.state === 'live' && document.querySelectorAll('#stream .para[data-seg]').length >= 1", timeout=30000)
    page.click("#send")
    shown = page.evaluate("document.getElementById('stream').textContent.length")
    page.wait_for_timeout(1500)
    check(page.evaluate("document.getElementById('stream').textContent.length") == shown and page.get_attribute("#status", "data-state") == "stopped", "stopped replay receives no more text")
    kept = page.locator("#stream .para[data-seg]").count()
    check(kept >= 1 and page.locator(f"{ACTIVE} g.s-node").count() == kept, f"analysis of the text received so far stays ({kept} paragraphs and steps)")
    check(page.locator(f"{ACTIVE} g.s-node.live").count() == 0, "no step is drawn as still in progress after stopping")
    page.select_option("#speed", "75")
    page.click("#send")
    page.wait_for_function("document.getElementById('status').dataset.state === 'done'", timeout=60000)
    check(page.text_content("#status").lower() == "terminado" and not page.is_visible("#chat-notice"), "a new send after a stop runs to the end")

    check(not errors, f"no page errors {errors}")
    b.close()
print("\nFAILURES:" if fails else "\nALL OK", *fails, sep="\n  ")
raise SystemExit(1 if fails else 0)
