import {isKeyboardActivation} from './interaction-intent';
import {requestFeedback} from './feedback';
import {openContact} from './contact';
import site from "../../content/site.json" with { type: "json" };
import "./certificates";
import { closeBooking } from "./booking";
import { showToast } from "./toast";
import {
  openDialog,
  closeDialog,
  reducedMotion,
} from "./motion";
const menu = document.querySelector<HTMLDialogElement>("#mobile-menu");
const menuButtons = [
  ...document.querySelectorAll<HTMLButtonElement>("[data-open-menu]"),
];
for (const button of menuButtons)
  button.addEventListener("click", () => {
    const open=!menu?.open;
    if (menu) {if(open)openDialog(menu);else void closeDialog(menu);}
    menuButtons.forEach((b) => b.setAttribute("aria-expanded", String(open)));
  });
menu?.addEventListener("close", () =>
  menuButtons.forEach((b) => b.setAttribute("aria-expanded", "false")),
);
document.addEventListener("click", (event) => {
  if (event.defaultPrevented) return;
  const target = event.target instanceof Element ? event.target : null;
  if (target?.closest("[data-dismiss]")) {
    const dialog = target.closest("dialog");
    if (dialog) void closeDialog(dialog);
  }
  const action = target?.closest<HTMLElement>("[data-contact],[data-book]");
  if (action) openContact(action.dataset.context ?? action.dataset.service ?? '');
});
for (const dialog of document.querySelectorAll<HTMLDialogElement>(
  "dialog:not([data-booking-drawer])",
)) {
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    void closeDialog(dialog);
  });
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (
      event.clientX < r.left ||
      event.clientX > r.right ||
      event.clientY < r.top ||
      event.clientY > r.bottom
    )
      void closeDialog(dialog);
  });
}
for (const button of document.querySelectorAll("[data-copy-promo]"))
  button.addEventListener("click", async () => {
    const code = (button as HTMLElement).dataset.promo || site.promo;
    try {
      await navigator.clipboard.writeText(code);
      showToast("Скопировано");
    } catch {
      showToast(`Не удалось скопировать. Промокод — ${code}`);
    }
  });
for (const gift of document.querySelectorAll<HTMLElement>("[data-gift]"))
  gift.addEventListener("click", () => {
    if (gift.dataset.hasPhoto === "true")
      gift.setAttribute(
        "aria-pressed",
        String(gift.getAttribute("aria-pressed") !== "true"),
      );
  });
// Local navigation closes overlays before native smooth scrolling starts.
document.addEventListener("click", async (event) => {
  if (event.defaultPrevented) return;
  const target = event.target instanceof Element ? event.target : null;
  const link = target?.closest<HTMLAnchorElement>('a[href]');
  if (
    !link ||
    link.classList.contains("skip") ||
    event.ctrlKey ||
    event.metaKey ||
    event.shiftKey ||
    event.altKey
  )
    return;
  const destination=new URL(link.href,location.href);
  const samePath=destination.pathname.replace(/\/$/,'')===location.pathname.replace(/\/$/,'');
  const homeAlias=destination.pathname==='/'&&!!document.querySelector('main > .hero#top');
  if(link.target&&link.target!=='_self'||link.hasAttribute('download')||destination.origin!==location.origin||destination.search!==location.search||!samePath&&!homeAlias)return;
  const hash = destination.hash;
  if(!hash)return;
  let section: HTMLElement | null;
  try {
    section = document.getElementById(decodeURIComponent(hash.slice(1)));
  } catch {
    return;
  }
  if (!section) return;
  event.preventDefault();
  requestFeedback('tap', event);
  await Promise.all(
    [...document.querySelectorAll<HTMLDialogElement>("dialog[open]")].map(
      (dialog) =>
        dialog.matches("[data-booking-drawer]")
          ? closeBooking()
          : closeDialog(dialog),
    ),
  );
  history.pushState(null, "", hash);
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  const targetHeading =
    section.querySelector<HTMLElement>(".section-title") ?? section;
  targetHeading.tabIndex = -1;
  targetHeading.focus({ preventScroll: true });
  const behavior = reducedMotion.matches || isKeyboardActivation(event) ? "instant" : "smooth";
  if (hash === "#top") window.scrollTo({ top: 0, behavior });
  else section.scrollIntoView({ behavior, block: "start" });
});
