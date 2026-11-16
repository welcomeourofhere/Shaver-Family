export function updateReadingEdges(element:HTMLElement){
 const style=getComputedStyle(document.documentElement),tolerance=parseFloat(style.getPropertyValue('--reading-scroll-tolerance')),fade=parseFloat(style.getPropertyValue('--size-16'));
 const range=element.scrollHeight-element.clientHeight,scrollable=range>tolerance;
 const above=scrollable&&element.scrollTop>1,below=scrollable&&element.scrollTop<range-1;
 for(const [key,value]of Object.entries({readingScrollable:scrollable,readingAbove:above,readingBelow:below}))if(element.dataset[key]!==String(value))element.dataset[key]=String(value);
 for(const [key,value]of Object.entries({'--reading-fade-top':above?Math.min(fade,element.scrollTop):0,'--reading-fade-bottom':below?Math.min(fade,range-element.scrollTop):0})){
  const pixels=`${value}px`;if(element.style.getPropertyValue(key)!==pixels)element.style.setProperty(key,pixels);
 }
}
