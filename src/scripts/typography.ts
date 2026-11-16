import {bindRuns,typographyBlocks as blocks,typographyExcludedSelector as excluded} from './typography-rules.ts';
export {bindRuns} from './typography-rules.ts';

if (typeof document !== "undefined") {
  const ownWrites = new WeakMap<Text, string>();
  const pending = new Set<Element>();
  let frame = 0;
  function apply(root: Element) {
    if (!root.isConnected || root.closest(excluded)) return;
    let run: Text[] = [];
    const flush = () => {
      const values = bindRuns(run.map(node => node.data),!!run[0]?.parentElement?.closest("h1,h2,h3,h4,h5,h6"));
      run.forEach((node, index) => {
        if (node.data !== values[index]) {
          ownWrites.set(node, values[index]);
          node.data = values[index];
        }
      });
      run = [];
    };
    const visit = (element: Element) => {
      for (const node of element.childNodes) {
        if (node instanceof Text) run.push(node);
        else if (node instanceof Element) {
          if (node.matches(excluded) || node.tagName === "BR") flush();
          else if (blocks.has(node.tagName.toLowerCase())) { flush(); visit(node); flush(); }
          else visit(node);
        }
      }
    };
    visit(root);
    flush();
  }
  function queue(node: Node) {
    let root = node instanceof Element ? node : node.parentElement;
    if (!root || root.closest(excluded)) return;
    while (root.parentElement && !blocks.has(root.tagName.toLowerCase())) root = root.parentElement;
    pending.add(root);
    if (!frame) frame = requestAnimationFrame(() => {
      frame = 0;
      const roots = [...pending];
      pending.clear();
      roots.filter(root => !roots.some(other => other !== root && other.contains(root))).forEach(apply);
    });
  }
  apply(document.body);
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === "characterData" && record.target instanceof Text) {
        if (ownWrites.get(record.target) === record.target.data) ownWrites.delete(record.target);
        else queue(record.target);
      } else record.addedNodes.forEach(queue);
    }
  });
  observer.observe(document.body, { subtree: true, childList: true, characterData: true });
  document.addEventListener("astro:before-swap", () => {
    observer.disconnect(); cancelAnimationFrame(frame); pending.clear();
  }, { once: true });
}
