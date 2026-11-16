import { numberToken } from "./motion";
import {popover} from './popover';
let timer: ReturnType<typeof setTimeout> | undefined,
  closing: ReturnType<typeof setTimeout> | undefined;
export function showToast(message: string) {
  const surface = document.querySelector<HTMLElement>("[data-toast]"),
    text = surface?.querySelector("[data-toast-message]");
  if (!surface || !text) return;
  clearTimeout(timer);
  clearTimeout(closing);
  const popup=popover(surface,document.body);popup.close();popup.open();
  text.replaceChildren(document.createTextNode(message));
  surface.classList.add("is-visible");
  timer = setTimeout(() => {
    surface.classList.remove("is-visible");
    closing = setTimeout(() => {
      popup.close();
    }, numberToken("--motion-ui"));
  }, numberToken("--toast-duration"));
}
