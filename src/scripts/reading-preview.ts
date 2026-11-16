/** Keep complete opening paragraphs, adding another when the first is only a short introduction. */
export function previewParagraphCount(paragraphs:readonly string[],minimum=100){
 let length=0,count=0;
 for(const paragraph of paragraphs){length+=paragraph.trim().length;count++;if(length>=minimum)break;}
 return count;
}
export function labelReadingButton(button:HTMLButtonElement,expanded:boolean){
 const label=expanded?'Показать фото':'Читать полностью';
 if(button.textContent!==label)button.textContent=label;
 button.setAttribute('aria-label',label);
 if(button.clientWidth&&button.scrollWidth>button.clientWidth+1)button.textContent=expanded?'К фото':'Читать';
}
