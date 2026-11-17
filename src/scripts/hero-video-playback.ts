type VideoMedia=Pick<HTMLVideoElement,'paused'|'play'|'pause'|'src'|'dataset'|'getAttribute'>;

/** Visibility updates share one play attempt; stale completion never changes the latest intent. */
export function heroVideoPlayback(video:VideoMedia){
 let wanted=false,pending=false,revision=0;
 const sync=(play:boolean)=>{
  if(!play){const stop=wanted||pending||!video.paused;wanted=false;pending=false;revision++;if(stop)video.pause();video.dataset.heroVideoPlayback='paused';return;}
  if(wanted&&(pending||!video.paused))return;
  wanted=true;pending=true;const attempt=++revision;video.dataset.heroVideoPlayback='pending';
  if(!video.getAttribute('src'))video.src=video.dataset.videoSrc!;
  try{
   void Promise.resolve(video.play()).then(()=>{
    if(attempt!==revision){if(!wanted)video.pause();return;}
    video.dataset.heroVideoPlayback=video.paused?'paused':'playing';
   }).catch(()=>{if(attempt===revision)video.dataset.heroVideoPlayback='blocked';})
   .finally(()=>{if(attempt===revision)pending=false;});
  }catch{if(attempt===revision){pending=false;video.dataset.heroVideoPlayback='blocked';}}
 };
 return {sync};
}
