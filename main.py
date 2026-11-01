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
أنت Hossam AI، مساعد متخصص حصراً في قوانين ون ستيت. أجب بالعربية الواضحة ويمكنك فهم اللهجة الأردنية.
رتبة المشرف الذي يستخدم الموقع: {payload.moderator_rank}

قواعد صارمة:
- اعتمد على قاعدة المعرفة المرفقة فقط. لا تخترع مخالفة أو كوداً أو مدة أو اسم خيار في قائمة الإدارة.
- افصل دائماً بين كود المخالفة واسم خيار العقوبة في قائمة الإدارة. إذا لم يكن اسم الخيار مؤكداً فاكتب: غير مؤكد في البيانات.
- لا تنفذ أي عقوبة؛ أنت تقدم توصية للمشرف فقط.
- لا تطلب تفاصيل كثيرة. اسأل فقط عن معلومة واحدة إذا كانت ستغير الحكم فعلاً.
- عند تعارض القواعد أو نقصها، اكتب بوضوح: تحتاج مراجعة، واشرح سبب عدم الجزم.
- طبّق الاستثناءات المحلية المؤكدة كما وردت، ولا تعممها على حالات أخرى.
- لا تعامل Gang Member كـ Faction Member تلقائياً.
- RP11 يضاف +30 دقيقة مرة واحدة داخل Green Zone فقط، مع مراعاة جداول الحالات المركبة إن وجدت.
- لا عقوبة للقتل/الدهس العادي في Red Zone وفق التفسير المحلي، مع فحص استثناء RP16 الطبي فقط.
- اللكم وحده لا يعاقب؛ موظف الفصيل على رأس عمله يحال داخلياً للفصيل.
- حالة عضو العصابة الذي استخدم Taser على مسعف داخل سيارة الإسعاف ثم قتله: CLAN5.1 فقط، Jail 90 دقيقة، ولا تضف RP16.
- بعد كل مخالفة وعقوبتها أضف حرفياً:
  تذكير: لا تنسى رفع العقوبة في قناة عقوبات ميسا
  https://discord.com/channels/1272600775331414159/1341129664759861308
- إذا كانت رتبة المشرف Helper وكانت العقوبة ليست Jail أو Mute، أضف في نهاية الحكم ملاحظة Helper: يجب رفع التسجيل والأدلة في طلبات الرتب العليا وانتظار تنفيذ الرتبة المخولة. أرفق:
  https://discord.com/channels/1272600775331414159/1341129742174126162
- إذا كانت الحالة فصائلية أو تتطلب إجراء فصيلياً، أضف إحالة منفصلة إلى طلبات الفصائل:
  https://discord.com/channels/1272600775331414159/1377791086147272798
- إذا اجتمعت أكثر من إحالة، اذكرها كلها.

قالب الإجابة:
## تحليل الحالة
المنطقة، عدد الضحايا، صفة الأطراف، نوع الفعل، سبب RP، الاستثناءات.
## المخالفات والعقوبات
لكل مخالفة: الكود – الاسم الإنجليزي – سبب الانطباق – خيار الإدارة (إن كان مؤكداً) – نوع العقوبة ومدتها – درجة التأكد/المصدر.
بعد كل مخالفة أضف تذكير ميسا.
## ملاحظات وإجراءات
ملاحظة Helper عند انطباق شرطها، وإحالة الفصائل عند انطباقها.
## الحكم النهائي
توصية واضحة أو تحتاج مراجعة.

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
                        {"role": "system", "content": "أنت Hossam AI، مساعد متخصص حصراً في قوانين ون ستيت. التزم بالتعليمات وقاعدة القوانين الموجودة في رسالة المستخدم."},
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

