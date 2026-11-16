import {test} from 'node:test';
import assert from 'node:assert/strict';
import {bindRuns} from '../src/scripts/typography.ts';

test('Russian short words bind across inline nodes without changing their lengths or markup', () => {
  assert.deepEqual(bindRuns(['В ', 'СОЮЗЕ ', 'и ', 'в ', 'Кирове']), ['В\u00a0','СОЮЗЕ ','и\u00a0','в\u00a0','Кирове']);
  assert.equal(bindRuns(['Стрижка в «СОЮЗЕ» и на каждый день'])[0], 'Стрижка в\u00a0«СОЮЗЕ» и\u00a0на\u00a0каждый день');
  assert.equal(bindRuns(['Слово, но не предлог внутри слова: основа ива'])[0], 'Слово, но\u00a0не\u00a0предлог внутри слова: основа ива');
  const input = ['На\u00a0карте\n', 'и ', 'в Кирове'];
  assert.deepEqual(bindRuns(bindRuns(input)), bindRuns(input));
  assert.equal(bindRuns(['На\nкарте'])[0], 'На\nкарте');
});

test('heading dash stays with the next word across inline runs without changing text length',()=>{
  assert.deepEqual(bindRuns(['Стиль — ', 'норма'],true),['Стиль —\u00a0','норма']);
  assert.equal(bindRuns(['Твой стиль — в хороших руках'],true)[0],'Твой стиль —\u00a0в\u00a0хороших руках');
  assert.equal(bindRuns(['Платим 500–1000, без разрыва'],true)[0],'Платим 500–1000, без\u00a0разрыва');
});

test('prices keep currency and percent signs with their amount across inline runs',()=>{
 assert.deepEqual(bindRuns(['От 500',' ₽ и 50',' %']),['От\u00a0500','\u00a0₽ и\u00a050','\u00a0%']);
 assert.equal(bindRuns(['500 ₽'])[0].length,5);
 assert.deepEqual(bindRuns(bindRuns(['от 500 ₽'])),bindRuns(['от 500 ₽']));
});

test('paired typographic quotes use guillemets across inline runs without changing run lengths',()=>{
 assert.deepEqual(bindRuns(['Барбершоп „','СОЮЗ','“']),['Барбершоп «','СОЮЗ','»']);
 assert.equal(bindRuns(['“Честная цена”'])[0],'«Честная цена»');
 const text=['„В ', 'СОЮЗЕ“'];
 assert.deepEqual(bindRuns(bindRuns(text)),bindRuns(text));
 assert.deepEqual(bindRuns(text).map(x=>x.length),text.map(x=>x.length));
});
