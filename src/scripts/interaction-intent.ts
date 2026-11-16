// Pointer release also has detail=0; only an actual click can be keyboard activation.
export function isKeyboardActivation(event?:{type:string;detail?:number}){
 return !!event&&(event.type==='keydown'||event.type==='keyup'||event.type==='keypress'||event.type==='click'&&event.detail===0);
}
// Unidentified, point-sized pointers can come from desktop accessibility/input drivers.
export function isMousePointer(event:{pointerType:string;width:number;height:number}){
 return event.pointerType==='mouse'||event.pointerType===''&&event.width===1&&event.height===1;
}
