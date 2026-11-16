import catalog from '../../content/work-photos.json' with {type:'json'};
import ownerCatalog from '../../content/work-photos-owner.json' with {type:'json'};
import titleCatalog from '../../content/work-photo-titles.json' with {type:'json'};
import team from '../../content/team.json' with {type:'json'};

const labels={haircuts:'Стрижки',beards:'Борода',kids:'Детские'};
const hash=/^[a-f0-9]{64}$/;
type WallPhoto=typeof catalog.photos[number];
type OwnerPhoto=typeof ownerCatalog.photos[number]|typeof ownerCatalog.duplicates[number];
type Provenance=(WallPhoto&{source:'vk-public-wall'})|OwnerPhoto;
type WorkPhoto=Pick<WallPhoto,'id'|'masterId'|'title'|'categories'|'variants'>&{provenance:Provenance[]};
type CreditOverride={vkId:string;masterId:string;evidence:string;sourceSha256:string;match:string;confirmed:boolean};
const validMaster=(id:string)=>team.masters.some(master=>master.id===id);
const unique=(values:string[])=>new Set(values).size===values.length;
const validVariants=(photo:WallPhoto|OwnerPhoto)=>photo.variants.length===3&&photo.variants.every((variant,index)=>variant.width===[360,720,1080][index]&&variant.url===`/media/works/${photo.id}-${variant.width}.webp`&&Number.isInteger(variant.height)&&variant.height>0&&Number.isInteger(variant.bytes)&&variant.bytes>0&&hash.test(variant.sha256));
const validPhoto=(photo:WallPhoto|OwnerPhoto)=>validMaster(photo.masterId)&&photo.title.trim()&&hash.test(photo.sourceSha256)&&photo.sourceWidth>0&&photo.sourceHeight>0&&photo.categories.length&&unique(photo.categories)&&photo.categories.every(category=>Object.hasOwn(labels,category));

// Only confirmed same-frame evidence joins sources; similarity never assigns a master.
export function mergeVerifiedWorks(wall:typeof catalog,owner:typeof ownerCatalog){
 if(wall.source!=='vk-public-wall'||wall.ownerId!==-210007626||!hash.test(wall.sourceSnapshotSha256)||!wall.photos.length)throw new Error('Invalid verified VK work catalog');
 if(owner.schemaVersion!==1||owner.source!=='owner-supplied'||owner.ownerCreditAuthority!==true||!owner.photos.length)throw new Error('Invalid verified owner work catalog');
 const rows:WorkPhoto[]=wall.photos.map(photo=>{
  if(!validPhoto(photo)||!validVariants(photo)||!photo.creditEvidence.trim()||!photo.captionEvidence.trim()
   ||![photo.photoId,photo.postId].every(id=>Number.isInteger(id)&&id>0)||!Number.isInteger(photo.albumId)||!(photo.albumId>0||photo.albumId===-7)
   ||photo.id!==`vk-${photo.photoId}`||photo.postUrl!==`https://vk.ru/wall-210007626_${photo.postId}`||photo.photoUrl!==`https://vk.ru/photo-210007626_${photo.photoId}`||!hash.test(photo.sourceTextSha256))throw new Error('Invalid verified VK work photograph: '+photo.id);
  return {id:photo.id,masterId:photo.masterId,title:photo.title,categories:photo.categories,variants:photo.variants,provenance:[{...photo,source:'vk-public-wall'}]};
 });
 const allOwner=[...owner.photos,...owner.duplicates];
 if(!unique(rows.map(photo=>photo.id))||!unique(allOwner.map(photo=>photo.id))||!unique(allOwner.map(photo=>photo.pixelSha256)))throw new Error('Duplicate verified work photo IDs or owner frames');
 for(const photo of allOwner){
  if(!validPhoto(photo)||photo.source!=='owner-supplied'||photo.status!=='verified-owner'||photo.id!==`owner-${photo.sourceSha256.slice(0,16)}`||!hash.test(photo.pixelSha256)
   ||photo.evidence.kind!=='owner-supplied-master-group'||photo.evidence.filename!==photo.ownerFilename||photo.evidence.masterId!==photo.masterId||photo.evidence.group!==photo.ownerGroup
   ||!Number.isInteger(photo.ownerIndex)||photo.ownerIndex<1||!Number.isInteger(photo.ownerGroup)||photo.ownerGroup<1||!photo.sourceFile.endsWith('/'+photo.ownerFilename)
   ||photo.frameMatches.some(match=>match.confirmed!==true||!['exact-pixels','visual-same-frame'].includes(match.match)||match.vkId!==`vk-${match.photoId}`||!hash.test(match.sourceSha256)))throw new Error('Invalid verified owner work photograph: '+photo.id);
 }
 const overrides=owner.overrides as CreditOverride[],usedOverrides=new Set<CreditOverride>();
 for(const photo of owner.duplicates){
  const existing=rows.find(row=>row.id===photo.duplicateOf),original=wall.photos.find(row=>row.id===photo.duplicateOf);
  const match=photo.frameMatches.find(frame=>frame.vkId===photo.duplicateOf&&frame.currentRuntime&&frame.confirmed);
  if(!existing||!original||photo.decision!=='reuse-existing-runtime'||photo.variants.length||!match||match.sourceSha256!==original.sourceSha256)throw new Error('Unconfirmed duplicate work photograph: '+photo.id);
  if(existing.masterId!==photo.masterId){
   const override=overrides.find(item=>item.vkId===existing.id&&item.masterId===photo.masterId&&item.evidence===photo.ownerFilename&&item.sourceSha256===photo.sourceSha256&&item.match===match.match&&item.confirmed===true);
   if(!override)throw new Error('Owner credit conflict requires explicit reviewed override: '+photo.id);
   existing.masterId=photo.masterId;usedOverrides.add(override);
  }
  existing.provenance.push(photo);
 }
 if(usedOverrides.size!==overrides.length)throw new Error('Unmatched owner credit override');
 for(const photo of owner.photos){
  if(!validVariants(photo)||photo.frameMatches.some(match=>match.currentRuntime||rows.some(row=>row.id===match.vkId))||rows.some(row=>row.id===photo.id))throw new Error('Invalid new owner work photograph: '+photo.id);
  rows.push({id:photo.id,masterId:photo.masterId,title:photo.title,categories:photo.categories,variants:photo.variants,provenance:[photo]});
 }
 return rows.map(photo=>{
  const master=team.masters.find(item=>item.id===photo.masterId)!,largest=photo.variants.at(-1)!;
  return {...photo,masterName:master.name,name:master.name.split(' ')[0],alt:`${photo.title} — ${master.name}`,caption:photo.title,src:largest.url,width:largest.width,height:largest.height};
 });
}
export function applyReviewedWorkTitles(photos:ReturnType<typeof mergeVerifiedWorks>,review:typeof titleCatalog){
 if(review.schemaVersion!==1||review.source!=='shaver-family-lookbook-visual-review'||!hash.test(review.catalogSource.sourceSha256)||!unique(review.catalog.map(style=>style.id))||!unique(review.photos.map(photo=>photo.id))||review.photos.length!==photos.length)throw new Error('Invalid reviewed work title catalog');
 const styles=new Map(review.catalog.map(style=>[style.id,style])),assessments=new Map(review.photos.map(photo=>[photo.id,photo]));
 if(review.catalog.some(style=>!style.en.trim()||!style.ru.trim()||!['hair','beard','element'].includes(style.type)))throw new Error('Invalid work style label');
 return photos.map(photo=>{
  const assessment=assessments.get(photo.id),style=assessment&&styles.get(assessment.primaryId);
  if(!assessment||!style||!assessment.basis.trim()||!['high','medium','low'].includes(assessment.confidence)||!['closest-family','catalog-fit'].includes(assessment.status)||!unique(assessment.secondaryIds)||assessment.secondaryIds.some(id=>id===assessment.primaryId||!styles.has(id))||assessment.viewLimits.some(limit=>!limit.trim()))throw new Error('Missing or invalid reviewed work title: '+photo.id);
  const title=`${style.en} (${('displayRu'in style?style.displayRu:undefined)??style.ru})`;
  return {...photo,title,caption:title,alt:`${title} — ${photo.masterName}`,titleAssessment:assessment};
 });
}
export const workPhotos=applyReviewedWorkTitles(mergeVerifiedWorks(catalog,ownerCatalog),titleCatalog);
export const worksSourceStatus='verified-combined';
export const workMasters=team.masters.filter(master=>workPhotos.some(photo=>photo.masterId===master.id));
export const workFilterMasters=team.masters;
export const workCategories=Object.entries(labels).filter(([id])=>workPhotos.some(photo=>photo.categories.includes(id))).map(([id,label])=>({id,label}));
export const workSequence=workPhotos;
