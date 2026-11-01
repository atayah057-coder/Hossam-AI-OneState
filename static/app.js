const message=document.getElementById('message'),send=document.getElementById('send'),rank=document.getElementById('rank'),counter=document.getElementById('counter'),error=document.getElementById('error'),result=document.getElementById('result'),answer=document.getElementById('answer');
message.addEventListener('input',()=>counter.textContent=`${message.value.length} / 5000`);
function renderAnswer(text){
  const escapeHtml=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let html=escapeHtml(text);
  html=html.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>');
  html=html.replace(/(https:\/\/discord\.com\/channels\/[0-9]+\/[0-9]+)/g,'<a class="discord-link" href="$1" target="_blank" rel="noopener noreferrer">فتح قناة Discord <span aria-hidden="true">↗</span></a>');
  html=html.replace(/^\s*[•-]\s?/gm,'<span class="bullet">•</span> ');
  answer.innerHTML=html;
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
