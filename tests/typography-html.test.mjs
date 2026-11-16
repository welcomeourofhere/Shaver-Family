import {test} from 'node:test';
import assert from 'node:assert/strict';
import {typographyHTML} from '../src/content/typography-html.ts';

test('initial HTML binds text across inline nodes without rewriting attributes, scripts or quotes',()=>{
 const html='<p class="in a" data-x="в Кирове">В <em>СОЮЗе</em> и в «Кирове» &amp; на карте</p><script>const a="в Кирове";</script><pre>в Кирове</pre><p data-typography="off">в Кирове</p>';
 const expected='<p class="in a" data-x="в Кирове">В\u00a0<em>СОЮЗе</em> и\u00a0в\u00a0«Кирове» &amp; на\u00a0карте</p><script>const a="в Кирове";</script><pre>в Кирове</pre><p data-typography="off">в Кирове</p>';
 assert.equal(typographyHTML(html),expected);assert.equal(typographyHTML(expected),expected);
});
test('heading, line break and price rules are identical before and after startup',()=>{
 assert.equal(typographyHTML('<h2>Стиль — <span>норма</span><br>жизни</h2><p>от 500 ₽</p>'),'<h2>Стиль —\u00a0<span>норма</span><br>жизни</h2><p>от\u00a0500\u00a0₽</p>');
 assert.equal(typographyHTML('<p>в <input value="Кирове"> городе</p>'),'<p>в <input value="Кирове"> городе</p>');
});
