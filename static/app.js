const message=document.getElementById('message'),send=document.getElementById('send'),rank=document.getElementById('rank'),counter=document.getElementById('counter'),error=document.getElementById('error'),result=document.getElementById('result'),answer=document.getElementById('answer');
message.addEventListener('input',()=>counter.textContent=`${message.value.length} / 5000`);
send.addEventListener('click',async()=>{
 const value=message.value.trim(); error.hidden=true;
 if(value.length<3){error.textContent='اكتب وصف الحالة أولاً.';error.hidden=false;return}
 send.disabled=true;send.textContent='جاري تحليل الحالة...';
 try{
  const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:value,moderator_rank:rank.value})});
  const data=await res.json();if(!res.ok)throw new Error(data.detail||'حدث خطأ غير متوقع');
  answer.textContent=data.answer;result.hidden=false;result.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(e){error.textContent=e.message;error.hidden=false}
 finally{send.disabled=false;send.innerHTML='تحليل الحالة <b>←</b>'}
});
document.getElementById('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(answer.textContent);document.getElementById('copy').textContent='تم النسخ ✓'}catch(e){document.getElementById('copy').textContent='تعذر النسخ'}});
