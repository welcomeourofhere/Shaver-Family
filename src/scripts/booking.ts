import {isKeyboardActivation} from './interaction-intent';
import { closeDialog, numberToken, textToken, reducedMotion } from "./motion";
import { bookingURLs,certificateURLs } from "./booking-url";
import { showToast } from "./toast";
import {setLoading} from './loading';
import {requestFeedback} from './feedback';

export interface BookingAction {
  form?: 'booking'|'certificate';
  bookingUrl?: string;
  service?: string;
  master?: string;
  promo?: string;
  context?: string;
}

const drawer = document.querySelector<HTMLDialogElement>(
  "[data-booking-drawer]",
);
const panel = drawer?.querySelector<HTMLElement>("[data-booking-panel]");
const backdrop = drawer?.querySelector<HTMLElement>("[data-booking-backdrop]");
const frame = drawer?.querySelector<HTMLIFrameElement>("[data-booking-frame]");
const status = drawer?.querySelector<HTMLElement>("[data-booking-status]");
const recovery = drawer?.querySelector<HTMLElement>("[data-booking-recovery]");
const provider=drawer?.querySelector<HTMLElement>('.booking-provider');
const root = document.documentElement;
const animations = new Map<HTMLElement, Animation>();
let wanted = false;
let revision = 0;
let trigger: HTMLElement | null = null;
let frameTimer: ReturnType<typeof setTimeout> | undefined;

export function bookingActionFrom(element: HTMLElement): BookingAction {
  return {
    form: element.dataset.bookingForm==='certificate'?'certificate':'booking',
    bookingUrl: element.dataset.bookingUrl,
    service: element.dataset.service,
    master: element.dataset.master,
    promo: element.dataset.promo,
    context: element.dataset.context,
  };
}

function selection(action: BookingAction): string {
  const clean = (value: unknown) =>
    typeof value === "string" ? value.trim() : "";
  return (
    clean(action.context) ||
    [
      clean(action.service) && `Услуга: ${clean(action.service)}`,
      clean(action.master) && `Мастер: ${clean(action.master)}`,
      clean(action.promo) && `Акция: ${clean(action.promo)}`,
    ]
      .filter(Boolean)
      .join("\n")
  );
}

function syncTriggers() {
  for (const button of document.querySelectorAll<HTMLElement>(
    "[data-booking]",
  )) {
    if(button.dataset.bookingForm==='certificate'){
      for(const name of ['aria-controls','aria-haspopup','aria-expanded'])button.removeAttribute(name);
      continue;
    }
    button.setAttribute("aria-controls", "booking-drawer");
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-expanded", String(wanted));
  }
}

function syncLayout() {
  if (!drawer?.open) return;
  const available = root.clientWidth;
  const docked =
    available - Math.min(available, numberToken("--booking-width")) >=
    numberToken("--booking-page-min");
  const layout = docked ? "docked" : "overlay";
  if (drawer.dataset.layout !== layout) {
    const focused = drawer.contains(document.activeElement)
      ? (document.activeElement as HTMLElement)
      : null;
    // A native modal owns focus and inertness on narrow screens; a docked form leaves the page usable.
    drawer.close();
    drawer.dataset.layout = layout;
    if (docked) drawer.show();
    else drawer.showModal();
    focused?.focus({ preventScroll: true });
  }
  drawer.setAttribute("aria-modal", String(!docked));
  root.dataset.bookingLayout = layout;
}

function stopMotion(element: HTMLElement) {
  const current = animations.get(element);
  if (!current) return;
  current.cancel();
  animations.delete(element);
}

function move(element: HTMLElement, opening: boolean, scrim = false) {
  const active = animations.has(element);
  const style = getComputedStyle(element);
  const from = {
    opacity: active ? style.opacity : opening ? "0" : "1",
    transform: scrim
      ? "none"
      : active
        ? style.transform
        : opening
          ? "translateX(100%)"
          : "translateX(0)",
  };
  stopMotion(element);
  if (reducedMotion.matches) return;
  const animation = element.animate(
    [
      from,
      {
        opacity: opening ? "1" : "0",
        transform: scrim
          ? "none"
          : opening
            ? "translateX(0)"
            : "translateX(100%)",
      },
    ],
    {
      duration: numberToken(opening?"--motion-panel":"--motion-dock-exit"),
      easing: textToken("--ease-drawer"),
      fill: "forwards",
    },
  );
  animations.set(element, animation);
  return animation.finished.catch(() => {});
}

function clearFrameTimer() {
  clearTimeout(frameTimer);
  frameTimer = undefined;
}

function loadingSlowly() {
  clearFrameTimer();
  if(provider)setLoading(provider,false);
  if (status) {
    status.hidden = false;
    status.textContent ="Загрузка занимает больше обычного. Можно повторить её или открыть запись отдельно.";
  }
  if (recovery) recovery.hidden = false;
}

function loadFrame(retry = false) {
  const url = drawer?.dataset.bookingUrl;
  if (!frame || !url || (frame.hasAttribute("src") && !retry)) return;
  clearFrameTimer();
  if(provider)setLoading(provider,true);
  if (status) {
    status.hidden = false;
    status.textContent ="Загружаем онлайн-запись…";
  }
  if (recovery) recovery.hidden = true;
  frameTimer = setTimeout(loadingSlowly, numberToken("--booking-load-timeout"));
  frame.src = url;
}

export async function openBooking(
  action: BookingAction | HTMLElement = {},
  source?: HTMLElement,
  immediate = false,
  event?: Event,
) {
  const button = action instanceof HTMLElement ? action : source;
  const requested = action instanceof HTMLElement ? bookingActionFrom(action) : action;
  const nextForm=requested.form??'booking';
  const destination=nextForm==='certificate'
    ?certificateURLs(requested.bookingUrl??drawer?.dataset.bookingCertificateUrl)
    :bookingURLs(requested.bookingUrl??drawer?.dataset.bookingDefaultUrl);
  if ((requested.bookingUrl||nextForm==='certificate') && !destination) {
    showToast(nextForm==='certificate'?"Не удалось открыть покупку сертификата":"Не удалось открыть ссылку записи");
    return;
  }
  if(nextForm==='certificate'){
    if(destination)window.open(destination.publicUrl,'_blank','noopener,noreferrer');
    if(event)requestFeedback('open',event);
    return;
  }
  if (!drawer || !panel || !backdrop) return;
  drawer.dataset.bookingForm='booking';
  if(event)requestFeedback('open',event);
  if(event)document.dispatchEvent(new CustomEvent('soyuz:booking-open',{detail:{master_id:requested.master,service_id:button?.dataset.serviceId??button?.closest<HTMLElement>('[data-service-id]')?.dataset.serviceId}}));
  if (destination) {
    if (drawer.dataset.bookingUrl !== destination.widgetUrl) {
      clearFrameTimer();
      drawer.dataset.bookingUrl = destination.widgetUrl;
      frame?.removeAttribute("src");
    }
    const external = drawer.querySelector<HTMLAnchorElement>(
      "[data-booking-external]",
    );
    if (external) external.href = destination.publicUrl;
  }
  const context = selection(requested);
  const contextBox = drawer.querySelector<HTMLElement>(
    "[data-booking-context]",
  );
  const contextText = drawer.querySelector<HTMLElement>(
    "[data-booking-selection]",
  );
  if (contextBox && contextText) {
    contextText.textContent = context;
    contextBox.hidden = !context;
  }
  if (button) trigger = button;
  else if (!drawer.contains(document.activeElement))
    trigger =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
  for (const other of document.querySelectorAll<HTMLDialogElement>(
    "dialog[open]",
  )) {
    if (other !== drawer) void closeDialog(other, true);
  }
  if (wanted) {
    loadFrame();
    return;
  }
  const current = ++revision;
  wanted = true;
  if (!drawer.open) {
    // Start nonmodal so syncLayout can select the correct native presentation.
    drawer.dataset.layout = "";
    drawer.show();
  }
  root.dataset.bookingState = "open";
  syncLayout();
  syncTriggers();
  drawer
    .querySelector<HTMLButtonElement>("[data-booking-close]")
    ?.focus({ preventScroll: true });
  loadFrame();
  if (!immediate)
    await Promise.all([move(panel, true), move(backdrop, true, true)]);
  if (current !== revision) return;
  stopMotion(panel);
  stopMotion(backdrop);
}

export async function closeBooking(immediate = false) {
  if (!drawer?.open || !panel || !backdrop || !wanted) return;
  const current = ++revision;
  wanted = false;
  root.dataset.bookingState = "closing";
  syncTriggers();
  if (!immediate)
    await Promise.all([move(panel, false), move(backdrop, false, true)]);
  if (current !== revision) return;
  stopMotion(panel);
  stopMotion(backdrop);
  drawer.close();
  root.dataset.bookingState = "closed";
  delete root.dataset.bookingLayout;
  const returnTo =
    trigger?.isConnected && trigger.getClientRects().length
      ? trigger
      : [
          ...document.querySelectorAll<HTMLElement>(
            ".header-book[data-booking],.mobile-nav-book[data-booking]",
          ),
          ...document.querySelectorAll<HTMLElement>("[data-booking]"),
        ].find(
          (button) =>
            !button.closest("dialog") && button.getClientRects().length,
        );
  returnTo?.focus({ preventScroll: true });
}

document.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  const button = target?.closest<HTMLElement>("[data-booking]");
  if (
    !button ||
    event.defaultPrevented ||
    event.button !== 0 ||
    event.ctrlKey ||
    event.metaKey ||
    event.shiftKey ||
    event.altKey
  )
    return;
  // Preserve the real external anchor, including the dock's delegated click.
  if(button.dataset.bookingForm==='certificate'&&button instanceof HTMLAnchorElement)return;
  event.preventDefault();
  void openBooking(button, undefined, isKeyboardActivation(event), event);
});

drawer?.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  if (target?.closest("[data-booking-close], [data-booking-backdrop]"))
    void closeBooking(isKeyboardActivation(event));
  if (target?.closest("[data-booking-retry]")) loadFrame(true);
});
drawer?.addEventListener(
  "cancel",
  (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    void closeBooking(true);
  },
  { capture: true },
);
drawer?.addEventListener("close", () => {
  if (drawer.open) return;
  // Shared navigation may close any dialog; release the booking layout in that path too.
  ++revision;
  wanted = false;
  if (panel) stopMotion(panel);
  if (backdrop) stopMotion(backdrop);
  root.dataset.bookingState = "closed";
  delete root.dataset.bookingLayout;
  syncTriggers();
});
document.addEventListener("keydown", (event) => {
  if (!wanted || !drawer?.open) return;
  if (event.key === "Escape") {
    event.preventDefault();
    void closeBooking(true);
    requestFeedback('close',event);
  }
  if (event.key !== "Tab" || drawer.dataset.layout !== "overlay") return;
  const controls = [
    ...drawer.querySelectorAll<HTMLElement>(
      'button:not(:disabled),a[href],iframe,[tabindex]:not([tabindex="-1"])',
    ),
  ].filter(
    (element) =>
      element.getClientRects().length &&
      !element.closest("[hidden],[inert]") &&
      getComputedStyle(element).visibility !== "hidden",
  );
  const first = controls[0],
    last = controls[controls.length-1];
  if (
    event.shiftKey &&
    (document.activeElement === first || document.activeElement === drawer)
  ) {
    event.preventDefault();
    last?.focus({ preventScroll: true });
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first?.focus({ preventScroll: true });
  }
});
frame?.addEventListener("load", () => {
  if (!frame.hasAttribute("src")) return;
  // Cross-origin load confirms a document, never available times or a completed booking.
  clearFrameTimer();
  if(provider)setLoading(provider,false);
  if (status) status.hidden = true;
  if (recovery) recovery.hidden = true;
});
frame?.addEventListener("error", loadingSlowly);
window.addEventListener("resize", syncLayout, { passive: true });
reducedMotion.addEventListener("change", () => {
  if (reducedMotion.matches)
    for (const animation of animations.values()) animation.finish();
});
document.addEventListener("astro:before-swap", () => {
  clearFrameTimer();
  void closeBooking(true);
});
syncTriggers();
