const message=document.getElementById('message'),send=document.getElementById('send'),rank=document.getElementById('rank'),counter=document.getElementById('counter'),error=document.getElementById('error'),result=document.getElementById('result'),answer=document.getElementById('answer');
message.addEventListener('input',()=>counter.textContent=`${message.value.length} / 5000`);
function renderAnswer(text){
  const esc=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const lines=text.split(/\r?\n/); let html='', inCard=false;
  const finish=()=>{if(inCard){html+='</section>';inCard=false}};
  for(let raw of lines){
    let line=raw.trim(); if(!line) continue;
    line=line.replace(/^[-•]\s*/, '');
    const heading=line.match(/^\*\*(RP\d+(?:\.\d+)?\s*[—-].*?)\*\*$/i) || line.match(/^(RP\d+(?:\.\d+)?\s*[—-].+)$/i);
    if(heading){finish();inCard=true;html+=`<section class="violation-card"><h4 class="violation-title">${esc(heading[1]||heading[0])}</h4>`;continue}
    if(/^\*\*(الإجراءات|ملاحظات|الحكم النهائي).*\*\*$/i.test(line)){finish();html+=`<h4 class="section-title">${esc(line.replace(/\*/g,''))}</h4>`;continue}
    let safe=esc(line).replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');
    safe=safe.replace(/(https:\/\/discord\.com\/channels\/[0-9]+\/[0-9]+)/g,'<a class="discord-link" href="$1" target="_blank" rel="noopener noreferrer">فتح قناة Discord ↗</a>');
    safe=safe.replace(/^Admin Panel:\s*(.*)$/i,'<span class="field-label admin-label">خيار البانيل</span><span class="field-value admin-value">$1</span>');
    safe=safe.replace(/^Punishment:\s*(.*)$/i,'<span class="field-label punishment-label">العقوبة</span><span class="field-value punishment-value">$1</span>');
    safe=safe.replace(/^Reason:\s*(.*)$/i,'<span class="field-label reason-label">السبب</span><span class="field-value reason-value">$1</span>');
    safe=safe.replace(/^تذكير:\s*(.*)$/,'<span class="field-label reminder-label">تذكير</span><span class="field-value reminder-value">$1</span>');
    if(/^(<span class="field-label|<a class="discord-link)/.test(safe)) html+=`<div class="result-row">${safe}</div>`;
    else html+=`<p class="result-line">${safe}</p>`;
  }
  finish(); answer.innerHTML=html;
}
send.addEventListener('click',async()=>{
 const value=message.value.trim(); error.hidden=true;
 if(value.length<3){error.textContent='اكتب وصف الحالة أولاً.';error.hidden=false;return}
 send.disabled=true;send.textContent='جاري التحليل...';
 try{
  const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:value,moderator_rank:rank.value})});
  const data=await res.json();if(!res.ok)throw new Error(data.detail||'حدث خطأ غير متوقع');
  renderAnswer(data.answer);result.hidden=false;result.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(e){error.textContent=e.message;error.hidden=false}
 finally{send.disabled=false;send.innerHTML='تحليل الحالة <b>←</b>'}
});
document.getElementById('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(answer.innerText);document.getElementById('copy').textContent='تم النسخ ✓'}catch(e){document.getElementById('copy').textContent='تعذر النسخ'}});
