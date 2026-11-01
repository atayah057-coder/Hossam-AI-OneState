import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx

ROOT = Path(__file__).parent
RULES_PATH = Path(os.getenv("RULES_PATH", ROOT / "rules_ar.txt"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

app = FastAPI(title="Hossam AI - OneState Rules", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

class ChatRequest(BaseModel):
    message: str = Field(min_length=3, max_length=5000)
    moderator_rank: str = "غير محدد"

class ChatResponse(BaseModel):
    answer: str

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="لم يتم إعداد GROQ_API_KEY في إعدادات الاستضافة.")
    if not RULES_PATH.exists():
        raise HTTPException(status_code=500, detail="ملف قاعدة القوانين غير موجود.")
    rules = RULES_PATH.read_text(encoding="utf-8")

    prompt = f"""
أنت Hossam AI، مساعد متخصص حصراً في قوانين OneState. أجب بعربية واضحة ومختصرة.
رتبة المشرف: {payload.moderator_rank}

قواعد إلزامية:
1) اعتمد على قاعدة المعرفة فقط. لا تخترع مخالفة أو عقوبة أو مدة.
2) لكل مخالفة اكتب اسمها الإنجليزي كما هو في كتالوج القوانين، وهذا الاسم نفسه هو خيار الإداري في البانيل.
   مثال: RP1 — Deathmatch | Admin Panel: Deathmatch.
   مثال: RP4 — Creating NRP Situations | Admin Panel: Creating NRP Situations.
3) ممنوع استخدام RepeatKill كخيار موحد أو كبديل لأسماء المخالفات. لا تستخدمه إطلاقاً كخيار بانيل؛ حتى لو ورد في أمثلة محلية قديمة، فهي معلومة متعارضة/ملغاة بالنسبة لاسم خيار البانيل.
4) افصل بين خيار البانيل وبين نوع العقوبة ومدتها. نوع العقوبة فقط يكون Jail أو Ban أو Mute أو غيرها إذا وردت حرفياً في القواعد.
5) لا تعرض جدولاً ولا مقدمة طويلة. أظهر كل مخالفة منطبقة فقط، ولا تحذف أي مخالفة مؤكدة أو إجراء مطلوب.
6) استخدم هذا التنسيق المختصر لكل مخالفة، كل معلومة في سطر مستقل:
   **RP1 — Deathmatch**
   Admin Panel: Deathmatch
   Punishment: Jail — 20 minutes
   Reason: سبب الانطباق بجملة قصيرة.
   إذا لم يكن خيار البانيل أو نوع العقوبة/مدتها مثبتاً، اكتب: غير محدد في القواعد. لا تخمّن.
7) بعد المخالفات أضف قسم **الإجراءات**، وضع تذكير MESA مرة واحدة فقط كرابط واضح، وأضف إحالات Helper أو الفصائل عند انطباقها. لا تكرر الرابط:
   - تذكير عقوبات MESA عند وجود عقوبة: https://discord.com/channels/1272600775331414159/1341129664759861308
   - إذا كان المشرف Helper وكانت العقوبة Ban: رفع التسجيل وانتظار الرتبة المخولة: https://discord.com/channels/1272600775331414159/1341129742174126162
   - إحالة الفصائل فقط إذا كانت الواقعة تتطلب إجراءً فصيلياً: https://discord.com/channels/1272600775331414159/1377791086147272798
8) لا تقل إن الحالة فصائلية لمجرد أن أحد الأطراف عضو فصيل.
9) لا تنفذ العقوبة؛ قدم توصية فقط. إذا نقصت معلومة تغير الحكم، اذكرها بسطر واحد.
10) طبّق الاستثناءات المحلية: RP11 يضاف +30 دقيقة مرة واحدة داخل Green Zone فقط؛ القتل العادي في Red Zone لا يعاقب وفق القواعد المحلية؛ إطلاق النار على مسعف أثناء الإنعاش RP16 = Ban 12h، ودون إنعاش = Jail 90m؛ واستثناء CLAN5.1 الخاص بالـTaser كما هو موضح في القاعدة.
11) لا تعامل Gang Member كـ Faction Member تلقائياً.

قاعدة المعرفة:
{rules}

وصف الحالة:
{payload.message}
"""
    try:
        with httpx.Client(timeout=httpx.Timeout(35.0, connect=10.0)) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "أنت Hossam AI. اسم المخالفة الإنجليزي هو نفسه خيار البانيل. لا تستخدم RepeatKill كخيار موحد. أخرج كل مخالفة منفصلة مع نوع العقوبة ومدتها فقط إذا كانا مؤكدين."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1800,
                },
            )
            if response.status_code >= 400:
                detail = response.text[:500]
                raise RuntimeError(f"Groq API {response.status_code}: {detail}")
            data = response.json()
        answer = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        if not answer:
            raise RuntimeError("Groq returned an empty response")
        return ChatResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"تعذر الحصول على رد من Groq: {str(exc)[:500]}")

