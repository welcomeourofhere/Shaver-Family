import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import media from '../content/hero-media.json' with {type:'json'};

test('lighter hero preserves the accepted source and delivers a faststart H.264 MP4',()=>{
 const source=readFileSync(media.output),playback=readFileSync('public'+media.playback.url),hash=b=>createHash('sha256').update(b).digest('hex');
 assert.equal(hash(source),media.outputSha256);
 assert.equal(hash(playback),media.playback.sha256);
 assert.equal(playback.length,media.playback.bytes);
 assert.ok(playback.length<source.length*.75);
 for(const key of ['duration','width','height','fps','audio'])assert.equal(media.playback[key],media[key]);
 const atoms=[];
 for(let offset=0;offset<playback.length;){const size=playback.readUInt32BE(offset);assert.ok(size>=8&&offset+size<=playback.length);atoms.push(playback.toString('ascii',offset+4,offset+8));offset+=size;}
 assert.equal(atoms[0],'ftyp');assert.ok(atoms.indexOf('moov')>0&&atoms.indexOf('moov')<atoms.indexOf('mdat'));
 assert.ok(playback.includes(Buffer.from('avc1')));
});
