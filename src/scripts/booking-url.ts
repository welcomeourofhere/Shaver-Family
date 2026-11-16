export function bookingURLs(
  value: unknown,
): { publicUrl: string; widgetUrl: string } | undefined {
  if (typeof value !== "string") return;
  try {
    const publicURL = new URL(value),
      match = /^[nb](\d+)\.yclients\.(?:ru|com)$/.exec(publicURL.hostname);
    if (
      publicURL.protocol !== "https:" ||
      !match ||
      publicURL.username ||
      publicURL.password ||
      publicURL.port
    )
      return;
    publicURL.hostname = `n${match[1]}.yclients.ru`;
    const widgetURL = new URL(publicURL);
    widgetURL.hostname = `b${match[1]}.yclients.ru`;
    return { publicUrl: publicURL.href, widgetUrl: widgetURL.href };
  } catch {
    return;
  }
}

export function certificateURLs(value:unknown):{publicUrl:string;widgetUrl:string}|undefined{
 if(typeof value!=='string')return;
 try{
  const url=new URL(value);
  if(url.protocol!=='https:'||!/^o\d+\.yclients\.ru$/.test(url.hostname)||url.username||url.password||url.port||!/^\/certificates\/?$/.test(url.pathname)||url.search||url.hash)return;
  return {publicUrl:url.href,widgetUrl:url.href};
 }catch{return;}
}
