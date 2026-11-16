// Adapted from Shaver Family src/shared/js/typography.js; preserve inline markup.
export const typographyBlocks=new Set('body main section article aside header footer nav div p h1 h2 h3 h4 h5 h6 li ul ol dl dt dd table thead tbody tfoot tr td th figure figcaption blockquote details summary button label'.split(' '));
export const typographyExcludedTags=new Set('script style pre code kbd samp textarea input select svg canvas noscript iframe'.split(' '));
export const typographyExcludedSelector=[...typographyExcludedTags,'[contenteditable]:not([contenteditable="false"])','[data-typography="off"]'].join(',');
const shortWords = "в|во|на|с|со|к|ко|у|о|об|обо|от|до|по|из|за|без|для|при|над|под|про|перед|и|а|но|не|ни";
const pattern = new RegExp("(" + shortWords + ")([ \\t]+)(?=[«„“\"(]*[\\p{L}\\p{N}])", "giu");
const wordEnd = /[\p{L}\p{N}_\u00ad]$/u;

export function bindRuns(runs: string[],heading=false): string[] {
  const source = runs.join("");
  const quoted=source.replace(/„([^„“]*)“/gu,'«$1»').replace(/“([^“”]*)”/gu,'«$1»');
  let bound = quoted.replace(pattern, (match, word, space, offset) =>
    wordEnd.test(source.slice(Math.max(0, offset - 2), offset))
      ? match : word + "\u00a0".repeat(space.length));
  if(heading)bound=bound.replace(/([—–])([ \t]+)(?=\S)/gu,(_,dash,space)=>dash+"\u00a0".repeat(space.length));
  bound=bound.replace(/(\d)([ \t]+)(?=[₽%])/gu,(_,digit,space)=>digit+'\u00a0'.repeat(space.length));
  let offset = 0;
  return runs.map(run => {
    const result = bound.slice(offset, offset + run.length);
    offset += run.length;
    return result;
  });
}

