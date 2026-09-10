import {readFile,readdir} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';

const site=path.resolve('site');
const privateKeys=new Set(['closing_account_usage','quota_before','quota_after','quota_start','quota_end','resetsAt','usedPercent','windowDurationMins','thread_id','threadId','turn_id','turnId','accountId','account_id','access_token','refresh_token','api_key','encrypted_content','reasoning_text','raw_reasoning','cwd','starts','event_counts']);
function inspectJson(value,file){if(Array.isArray(value))value.forEach(v=>inspectJson(v,file));else if(value&&typeof value==='object')for(const[k,v]of Object.entries(value)){assert(!privateKeys.has(k),`Private field ${k} in ${file}`);inspectJson(v,file);}}
const patterns=[/\bsk-[A-Za-z0-9_-]{20,}\b/,/\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b/,/-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----/,/\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b/,/\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i,/[A-Z]:[\\/]+Users[\\/]/i];
async function walk(dir){const result=[];for(const ent of await readdir(dir,{withFileTypes:true})){const f=path.join(dir,ent.name);if(ent.isDirectory())result.push(...await walk(f));else result.push(f);}return result;}
const files=await walk(site);
for(const file of files){assert(['.html','.css','.js','.json','.svg','.md','.txt'].includes(path.extname(file)),`Unexpected deployed file: ${file}`);const text=await readFile(file,'utf8');for(const p of patterns)assert(!p.test(text),`Sensitive pattern in ${path.relative(site,file)}`);if(file.endsWith('.json'))inspectJson(JSON.parse(text),path.relative(site,file));}
const ledger=JSON.parse(await readFile(path.join(site,'data/ledger.json'),'utf8'));
assert(ledger.experiments.length>0);
const ids=new Set();
for(const e of ledger.experiments){assert(!ids.has(e.id));ids.add(e.id);assert(/^exp-\d{3}$/.test(e.id));assert(['completed','registered','running','stopped'].includes(e.status));assert(Number.isInteger(e.decisions)&&e.decisions>=0);assert(e.title&&e.question&&e.finding&&e.setup&&e.limitations);for(const key of ['data','protocol','report'])if(e[key]?.startsWith('/')){const f=path.resolve(site,'.'+e[key]);assert(f.startsWith(site+path.sep));await readFile(f);}if(e.results){assert(e.results.columns.length>0);for(const row of e.results.rows)assert.equal(row.length,e.results.columns.length);}}
const htmlFiles=files.filter(file=>path.extname(file)==='.html');
const indexHtml=await readFile(path.join(site,'index.html'),'utf8');
for(const id of ['theme','search','status','experiment-list','experiment','error','updated','study-count','decision-count','complete-count'])assert(indexHtml.includes(`id="${id}"`),`Missing UI target ${id}`);
function resolveLocalLink(file,url){
  const clean=url.split('#')[0].split('?')[0];
  if(!clean || clean.startsWith('http:') || clean.startsWith('https:') || clean.startsWith('mailto:') || clean.startsWith('tel:') || clean.startsWith('data:') || clean.startsWith('javascript:'))return null;
  const target=clean.startsWith('/') ? path.join(site,clean==='/'?'index.html':clean.slice(1)) : path.resolve(path.dirname(file),clean);
  const resolved=path.resolve(target);
  assert(resolved===site || resolved.startsWith(site+path.sep),`Local link escapes site: ${url}`);
  return resolved;
}
for(const file of htmlFiles){
  const text=await readFile(file,'utf8');
  for(const match of text.matchAll(/(?:href|src)="([^"]+)"/g)){
    const target=resolveLocalLink(file,match[1]);
    if(target)await readFile(target);
  }
}
for(const key of ['data','protocol','report','originalData','extensionProtocol']){
  for(const e of ledger.experiments){
    if(e[key] && typeof e[key]==='string' && e[key].startsWith('/')){
      const f=path.resolve(site,'.'+e[key]);
      assert(f===site || f.startsWith(site+path.sep),`Ledger ${key} escapes site`);
      await readFile(f);
    }
  }
}
for(const file of files.filter(file=>path.extname(file)==='.js')){
  const syntax=spawnSync(process.execPath,['--check',file],{stdio:'inherit'});
  assert.equal(syntax.status,0,`JavaScript syntax check failed: ${path.relative(site,file)}`);
}
console.log(`Release checks passed: ${files.length} static files; ${ledger.experiments.length} experiments; local links, JSON fields, credential patterns, and script syntax checked.`);
