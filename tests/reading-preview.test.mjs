import test from 'node:test';
import assert from 'node:assert/strict';
import {previewParagraphCount} from '../src/scripts/reading-preview.ts';
test('reading previews keep complete opening paragraphs and include a short introduction with the next paragraph',()=>{
 assert.equal(previewParagraphCount(['a'.repeat(130),'b'.repeat(280)]),1);
 assert.equal(previewParagraphCount(['a'.repeat(35),'b'.repeat(200),'c'.repeat(100)]),2);
 assert.equal(previewParagraphCount(['a'.repeat(20),'b'.repeat(20),'c'.repeat(80)]),3);
 assert.equal(previewParagraphCount([]),0);
});
