// The «Fuente» menu with an icon per source (a native <select> cannot show
// images). The hidden <select> stays the source of truth: choosing here sets
// its value and fires its "change" event, so the rest of the dashboard reads
// the source exactly as before. Keyboard: arrows, Home/End, Enter or Space to
// choose, Escape to close; focus returns to the button.
import { sourceIcon } from "./brand";
import { esc } from "./util";

export class SourceMenu {
  private button: HTMLButtonElement;
  private list: HTMLUListElement;

  constructor(
    host: HTMLElement,
    private select: HTMLSelectElement,
    labelledBy: string,
  ) {
    host.classList.add("src-menu");
    host.innerHTML =
      `<button type="button" class="src-button" aria-haspopup="listbox" aria-expanded="false"></button>` +
      `<ul class="src-list" role="listbox" tabindex="-1" hidden></ul>`;
    this.button = host.querySelector("button")!;
    this.list = host.querySelector("ul")!;
    // Read as "Fuente, DeepSeek Flash": the field's label, then the chosen source.
    this.button.id = `${select.id}-button`;
    this.button.setAttribute("aria-labelledby", `${labelledBy} ${this.button.id}`);
    this.list.setAttribute("aria-labelledby", labelledBy);
    this.button.addEventListener("click", () => (this.list.hidden ? this.open() : this.close(true)));
    this.button.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        this.open();
      }
    });
    this.list.addEventListener("keydown", (e) => this.key(e));
    this.list.addEventListener("click", (e) => {
      const li = (e.target as HTMLElement).closest<HTMLLIElement>("li[role='option']");
      if (li && li.getAttribute("aria-disabled") !== "true") this.choose(li.dataset.value!);
    });
    select.addEventListener("change", () => this.refresh());
    this.refresh();
  }

  /** Redraw from the <select> (call after its options change). */
  refresh(): void {
    const options = [...this.select.options];
    const current = this.select.selectedOptions[0];
    this.button.innerHTML =
      `${sourceIcon(this.select.value)}<span class="src-text">${esc(current?.text ?? "")}</span>` +
      `<svg class="src-chevron" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    this.list.replaceChildren(
      ...options.map((o) => {
        const li = document.createElement("li");
        li.role = "option";
        li.id = `${this.select.id}-opt-${o.value}`;
        li.dataset.value = o.value;
        li.tabIndex = -1;
        li.setAttribute("aria-selected", String(o.value === this.select.value));
        if (o.disabled) li.setAttribute("aria-disabled", "true");
        li.innerHTML = `${sourceIcon(o.value)}<span>${esc(o.text)}</span>`;
        return li;
      }),
    );
  }

  private items(): HTMLLIElement[] {
    return [...this.list.querySelectorAll<HTMLLIElement>("li[role='option']")];
  }

  private open(): void {
    this.list.hidden = false;
    this.button.setAttribute("aria-expanded", "true");
    document.addEventListener("pointerdown", this.outside, true);
    (this.items().find((li) => li.getAttribute("aria-selected") === "true") ?? this.items()[0])?.focus();
  }

  private close(focusButton: boolean): void {
    this.list.hidden = true;
    this.button.setAttribute("aria-expanded", "false");
    document.removeEventListener("pointerdown", this.outside, true);
    if (focusButton) this.button.focus();
  }

  private outside = (e: PointerEvent) => {
    if (!this.button.parentElement!.contains(e.target as Node)) this.close(false);
  };

  private choose(value: string): void {
    this.close(true);
    if (value === this.select.value) return;
    this.select.value = value;
    this.select.dispatchEvent(new Event("change", { bubbles: true }));
  }

  private key(e: KeyboardEvent): void {
    const enabled = this.items().filter((li) => li.getAttribute("aria-disabled") !== "true");
    const i = enabled.indexOf(document.activeElement as HTMLLIElement);
    const go = (j: number) => enabled[(j + enabled.length) % enabled.length]?.focus();
    switch (e.key) {
      case "ArrowDown": go(i + 1); break;
      case "ArrowUp": go(i - 1); break;
      case "Home": go(0); break;
      case "End": go(enabled.length - 1); break;
      case "Enter":
      case " ": {
        const li = document.activeElement as HTMLLIElement;
        if (li?.dataset.value && li.getAttribute("aria-disabled") !== "true") this.choose(li.dataset.value);
        break;
      }
      case "Escape": this.close(true); break;
      case "Tab": this.close(false); return;
      default: return;
    }
    e.preventDefault();
  }
}
