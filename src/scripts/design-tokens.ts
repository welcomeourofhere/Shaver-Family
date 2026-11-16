/** Read document-owned design tokens without initializing browser motion listeners. */
export function numberToken(name:string):number{
  const value=parseFloat(getComputedStyle(document.documentElement).getPropertyValue(name));
  if(!Number.isFinite(value))throw new Error(`Missing design token: ${name}`);
  return value;
}

export function textToken(name:string):string{
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
