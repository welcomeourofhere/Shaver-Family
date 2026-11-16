import source from "./design.json" with { type: "json" };
import { springCSS, drawerSpringCSS, windowSpringCSS, popoverSpringCSS } from './spring.ts';

const { unit, goldenRatio, dimensions } = source.scale;
const length = (steps: number) => `${Number((unit * steps).toFixed(6))}px`;

// Quarter steps retain optical type sizes; layout uses whole 4 px modules.
const roundModule = (value: number) => length(Math.round(value / unit));
const fraction = (power:number) => Number((goldenRatio ** -power).toFixed(6));
const zoom = (power:number) => String(Number((1 + goldenRatio ** -power).toFixed(6)));
const primitives = Object.fromEntries(
  dimensions.map((size) => [`--size-${size}`, length(size / 4)]),
);
export default {
  base: {
    ...primitives,
    "--unit": length(1),
    "--golden-ratio": String(goldenRatio),
    "--radius-card": length(6),
    "--radius-control": length(3),
    "--hero-top-space": length(10),
    "--popover-distance": length(-3),
    "--story-columns": `minmax(0, ${goldenRatio}fr) minmax(0, 1fr)`,
    "--split-columns": `minmax(0, 1fr) minmax(0, ${goldenRatio}fr)`,
    "--gift-certificate-weight": `${3 / goldenRatio}fr`,
    "--team-photo-base-scale":zoom(8),
    "--review-photo-scale":zoom(6),
    "--team-photo-scale":zoom(6),
    "--team-photo-press-scale":zoom(9),
    "--offer-photo-zoom":zoom(8),
    "--offer-photo-hover-zoom":zoom(9),
    "--certificate-selected-scale":zoom(5),
    "--certificate-wave-delay":`${Math.round(unit * goldenRatio ** 5)}ms`,
    "--certificate-depth-scale-step":String(fraction(8)),
    "--certificate-width-ratio":String(fraction(1)),
    "--certificate-row-span":String(Number((goldenRatio ** 2).toFixed(6))),
    "--about-depth-scale-step":String(fraction(8)),
    "--certificate-overhang": roundModule(unit * goldenRatio ** 6),
    "--gift-icon-size": `${(100 / goldenRatio) * 0.7}%`,
    ...source.base,
    "--ease-spring": springCSS,
    "--ease-drawer-spring": drawerSpringCSS,
    "--ease-window-spring": windowSpringCSS,
    "--ease-popover-spring": popoverSpringCSS,
  },
  responsive: source.responsive,
  dark:source.dark,
  theme:source.theme,
  selectionBySurface:source.selectionBySurface,
  actionBySurface:source.actionBySurface,
};
