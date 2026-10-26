const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function harness(file) {
  const nodes = new Map();
  function node() { return { style:{}, classList:{add(){},remove(){},contains(){return false;}}, listeners:{}, innerHTML:'', addEventListener(type,fn){this.listeners[type]=fn;}, querySelector(){return node();}, querySelectorAll(){return [];}, appendChild(){} }; }
  const get = id => {if(!nodes.has(id)) nodes.set(id,node()); return nodes.get(id);};
  const context = {document:{body:node(),getElementById:get,addEventListener(){},createElement:node},localStorage:{getItem(){return null;},setItem(){}},setInterval(){},setTimeout(){},console};
  vm.runInNewContext(fs.readFileSync(file,'utf8'),context);
  return {context,nodes};
}
const attack = '<img src=x onerror=alert(1)>\"\'&';
const result = {prediction:attack,confidence:0.8,characteristics:{[attack]:attack},reasoning:attack,recommendations:[attack],clinical_insights:{common_morphology:attack,similar_cases:attack,stage_distribution:{[attack]:1}}};
for(const file of ['static/js/main.js','templates/static/js/main.js']) {
  test(`${file}: analysis output escapes text and does not serialize model data into handlers`,()=>{
    const {context,nodes}=harness(path.join(__dirname,'..',file));
    context.displayResult(result);
    const html=nodes.get('result').innerHTML;
    assert.ok(!html.includes('<img src=x'));
    assert.ok(html.includes('&lt;img'));
    assert.ok(!/onclick=.*exportReport/.test(html));
  });
  test(`${file}: saved history cannot inject markup or event handlers`,()=>{
    const {context,nodes}=harness(path.join(__dirname,'..',file));
    context.saveToHistory(result);
    const html=nodes.get('history-container').innerHTML;
    assert.ok(!html.includes('<img src=x'));
    assert.ok(!html.includes('onclick='));
  });
}
