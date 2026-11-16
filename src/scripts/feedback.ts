import config from "../config/feedback.json" with { type: "json" };
export const FEEDBACK_STORAGE_KEY = "soyuz_feedback_enabled";
export const FEEDBACK_INTERVAL = config.intervalMs;
export const FEEDBACK_TONES = config.tones;
export const FEEDBACK_KINDS = [
  "filled",
  "text",
  "icon",
  "media",
  "disclosure",
  "selection",
] as const;
export type FeedbackKind = (typeof FEEDBACK_KINDS)[number];
type FeedbackTone = keyof typeof FEEDBACK_TONES;
let playRequested: ((tone: FeedbackTone, event: Event) => void) | undefined;
const handledEvents = new WeakSet<Event>();
const activations = new WeakMap<Event, { expanded: boolean; pointerType: string }>();

export function requestFeedback(tone: FeedbackTone, event: Event) {
  if (!event.isTrusted || handledEvents.has(event)) return;
  handledEvents.add(event);
  playRequested?.(tone, event);
}

export function readFeedbackPreference(
  storage: Pick<Storage, "getItem">,
): boolean {
  try {
    return storage.getItem(FEEDBACK_STORAGE_KEY) !== "false";
  } catch {
    return true;
  }
}
export function saveFeedbackPreference(
  storage: Pick<Storage, "setItem">,
  enabled: boolean,
): void {
  try {
    storage.setItem(FEEDBACK_STORAGE_KEY, String(enabled));
  } catch {
    /* Keep the current choice in memory. */
  }
}
export function canPlayFeedback(now: number, previous: number): boolean {
  return Number.isFinite(now) && now - previous >= FEEDBACK_INTERVAL;
}
export function canVibrateFeedback(
  event: { isTrusted: boolean; pointerType?: string },
  reducedMotion: boolean,
): boolean {
  return event.isTrusted && !reducedMotion &&
    (event.pointerType === "touch" || event.pointerType === "pen");
}
export function feedbackTone(
  kind: FeedbackKind,
  expanded = false,
): "tap" | "select" | "open" | "close" {
  if (kind === "disclosure") return expanded ? "close" : "open";
  return kind === "selection" || kind === "media" ? "select" : "tap";
}
export function classifyFeedback(control: HTMLElement): FeedbackKind {
  const explicit = control.dataset.uiKind;
  if (FEEDBACK_KINDS.includes(explicit as FeedbackKind))
    return explicit as FeedbackKind;
  if (control.matches('summary,[aria-expanded]')) return "disclosure";
  if (
    control.matches(
      "[data-gift],[data-certificate],.gift-visual,.certificate-object",
    )
  )
    return "media";
  if (control.matches('[role="tab"],[role="option"],[aria-pressed],[aria-selected],[data-rail-step],[data-dock-category]'))
    return "selection";
  if (control.matches(".icon-btn,.sd-arrow,[data-rail],[data-dismiss]"))
    return "icon";
  if (control.matches(".btn,.header-book,[data-contact],[data-book]"))
    return "filled";
  return "text";
}
export function controlFeedbackTone(control: HTMLElement, expanded: boolean): FeedbackTone {
  if (control.matches('[data-dismiss],[data-booking-close]')) return 'close';
  if (control.matches('[aria-haspopup="dialog"],[data-booking],[data-contact],[data-team-open],[data-open-menu],[data-dock-open],[data-open-reviews]'))
    return expanded ? 'close' : 'open';
  return feedbackTone(classifyFeedback(control), expanded);
}

if (typeof document !== "undefined") {
  // Accessing localStorage itself can throw before getItem is called.
  let storage: Storage | undefined;
  try {
    storage = window.localStorage;
  } catch {
    /* Preferences remain usable for this visit. */
  }
  let enabled = storage ? readFeedbackPreference(storage) : true;
  let lastPlayed = -Infinity;
  const players = new Map<FeedbackTone, HTMLAudioElement>();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const toggles = () =>
    document.querySelectorAll<HTMLButtonElement>("[data-feedback-toggle]");
  function updateSettings() {
    for (const toggle of toggles()) {
      toggle.setAttribute("aria-pressed", String(enabled));
      toggle.setAttribute(
        "aria-label",
        `Звук и вибрация: ${enabled ? "включены" : "выключены"}`,
      );
      const status = toggle.querySelector("[data-feedback-status]");
      if (status) status.textContent = enabled ? "вкл." : "выкл.";
    }
  }
  function stopFeedback() {
    for (const player of players.values()) {
      player.pause();
      player.currentTime = 0;
    }
    try {
      navigator.vibrate?.(0);
    } catch {
      /* Haptics are optional. */
    }
  }
  function prepareAudio() {
    if (!enabled || players.size) return;
    for (const tone of Object.keys(FEEDBACK_TONES) as FeedbackTone[]) {
      try {
        const player = new Audio(FEEDBACK_TONES[tone].url);
        player.preload = 'auto';
        player.volume = config.volume;
        players.set(tone, player);
      } catch { /* Visual controls work without audio support. */ }
    }
  }
  function play(tone: FeedbackTone, event: Event) {
    const now = performance.now();
    if (!enabled || !canPlayFeedback(now, lastPlayed)) return;
    lastPlayed = now;
    try {
      prepareAudio();
      for (const audio of players.values()) audio.pause();
      const player = players.get(tone);
      if (player) {
        player.currentTime = 0;
        void player.play().catch(() => {});
      }
    } catch {
      /* Unsupported or blocked media never prevents an action. */
    }
    // Touch/pen activation only; scrolling and mouse clicks do not vibrate.
    const pointerType = activations.get(event)?.pointerType ||
      ('pointerType' in event ? String(event.pointerType) : event.type === 'touchend' ? 'touch' : '');
    if (canVibrateFeedback({ isTrusted: event.isTrusted, pointerType }, reducedMotion.matches)) {
      try {
        navigator.vibrate?.(FEEDBACK_TONES[tone].hapticPattern);
      } catch {
        /* Unsupported browsers keep visual feedback. */
      }
    }
  }
  playRequested = play;
  let pointerStates = new WeakMap<HTMLElement, { expanded: boolean; pointerType: string }>();
  const selector = 'button,a[href],summary,input[type="checkbox"],input[type="radio"]';
  const controlFor = (target: EventTarget | null) => target instanceof Element ? target.closest<HTMLElement>(selector) : null;
  const expandedState = (control: HTMLElement) => control.matches('summary')
    ? !!control.parentElement?.hasAttribute('open')
    : control.getAttribute('aria-expanded') === 'true';
  document.addEventListener('pointerdown', event => {
    pointerStates = new WeakMap();
    const label = event.target instanceof Element ? event.target.closest('label') : null;
    const control = controlFor(event.target) || (label?.control?.matches('input[type="checkbox"],input[type="radio"]') ? label.control : null);
    if (control) pointerStates.set(control, { expanded: expandedState(control), pointerType: event.pointerType });
  }, {capture: true, passive: true});
  document.addEventListener('keydown', () => { pointerStates = new WeakMap(); }, {capture: true});
  document.addEventListener('pointercancel', () => { pointerStates = new WeakMap(); }, {capture: true, passive: true});
  document.addEventListener('click', event => {
    const control = controlFor(event.target);
    if (!control) return;
    const pointer = pointerStates.get(control);
    activations.set(event, {
      expanded: pointer?.expanded ?? expandedState(control),
      pointerType: event.pointerType || pointer?.pointerType || '',
    });
    pointerStates.delete(control);
  }, {capture: true});
  // Window bubbling follows component/document cancellation and retains native user activation.
  window.addEventListener(
    "click",
    (event) => {
      if (!event.isTrusted || event.defaultPrevented || event.button !== 0)
        return;
      const target = event.target instanceof Element ? event.target : null;
      if (
        !target ||
        target.closest('textarea,select,input:not([type="checkbox"]):not([type="radio"]),[contenteditable="true"]')
      )
        return;
      const control = controlFor(target);
      if (
        !control ||
        control.closest(
          '[disabled],[aria-disabled="true"],[inert],[data-feedback="off"],[data-feedback="manual"]',
        )
      )
        return;
      const expanded = activations.get(event)?.expanded ?? expandedState(control);
      const tone = controlFeedbackTone(control, expanded);
        if (control.matches("[data-feedback-toggle]")) {
          enabled = !enabled;
          if (storage) saveFeedbackPreference(storage, enabled);
          updateSettings();
          if (enabled) {
            prepareAudio();
            lastPlayed = -Infinity;
            requestFeedback("tap", event);
          } else stopFeedback();
          return;
        }
        requestFeedback(tone, event);
    },
  );
  window.addEventListener("storage", (event) => {
    if (event.key !== null && event.key !== FEEDBACK_STORAGE_KEY) return;
    enabled = storage ? readFeedbackPreference(storage) : enabled;
    if (!enabled) stopFeedback();
    updateSettings();
  });
  window.addEventListener("pagehide", stopFeedback);
  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) {
      try { navigator.vibrate?.(0); } catch { /* Haptics are optional. */ }
    }
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stopFeedback();
  });
  updateSettings();
  document.addEventListener('pointerdown',prepareAudio,{capture:true,passive:true,once:true});
  document.addEventListener('keydown',prepareAudio,{capture:true,once:true});
}
