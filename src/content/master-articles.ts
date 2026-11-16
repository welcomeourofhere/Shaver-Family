export interface StoryImage {alt:string;source:string;sourceSha256:string;variants:{url:string;width:number;height:number;sha256:string}[]}
export type StoryBlock = {kind:'qa';id:string;question:string;paragraphs:string[];sourceLine:number} | {kind:'photos';images:string[];caption:string} | {kind:'text';paragraphs:string[];sourceLine:number;quoted?:boolean;heading?:boolean};
export interface MasterStory {
  schemaVersion:number;slug:string;masterId:string;title:string;description:string;cover:string;
  lead?:string[];coverCaption?:string;
  sections:{id:string;title:string;intro?:string[];blocks:StoryBlock[]}[];
  closing:{title:string;paragraphs:string[]};
  source:{kind:string;file:string;sha256:string};
  media:Record<string,StoryImage>;
}
const files=import.meta.glob('../../content/master-articles/*.json',{eager:true,import:'default'});
export const masterStories=Object.entries(files)
  .filter(([path])=>!path.endsWith('.media.json'))
  .map(([path,article])=>({...article as Omit<MasterStory,'media'>,media:files[path.replace(/\.json$/,'.media.json')] as MasterStory['media']}));
