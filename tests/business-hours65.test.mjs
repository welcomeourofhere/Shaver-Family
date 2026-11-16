import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {businessStatus} from '../src/scripts/business-clock.ts';

const site=JSON.parse(readFileSync(new URL('../content/site.json',import.meta.url),'utf8'));
test('SOYUZ hours use confirmed 11–22 Moscow schedule and exact semantic countdown',()=>{
 assert.equal(site.hours,'11:00–22:00');
 for(const [time,state,heading,detail] of [
  ['00:33','closed','Сейчас закрыто','Откроемся через 7 ч 27 мин'],
  ['07:59','closed','Сейчас закрыто','Откроемся через 1 мин'],
  ['08:00','open','Сейчас открыто','До закрытия 11 ч'],
  ['16:59','open','Сейчас открыто','До закрытия 2 ч 1 мин'],
  ['17:00','closing','Сейчас открыто','До закрытия 2 ч'],
  ['18:59','closing','Сейчас открыто','До закрытия 1 мин'],
  ['19:00','closed','Сейчас закрыто','Откроемся через 13 ч'],
 ]){
  const value=businessStatus(new Date(`2026-11-16T${time}:00Z`),site.hours);
  assert.equal(value.state,state);assert.equal(value.heading,heading);assert.equal(value.detail,detail);
 }
});
