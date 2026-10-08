import fs from 'node:fs/promises';
import {prepareFeed} from './news_images.mjs';
const name='data/feed.json';
const feed=await prepareFeed(JSON.parse(await fs.readFile(name,'utf8')));
await fs.writeFile(name+'.tmp',JSON.stringify(feed,null,2)+'\n');
await fs.rename(name+'.tmp',name);
console.log(`Prepared ${feed.items.length} news photos with responsive WebP variants`);
