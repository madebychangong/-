from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from korean_lunar_calendar import KoreanLunarCalendar
import google.generativeai as genai
import os

# API 키는 Vercel 환경변수에서 가져옵니다 (보안)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# 가성비 좋은 모델 선택 (목록에 안보여도 API 호출은 됩니다!)
MODEL_NAME = "gemini-1.5-flash"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SajuRequest(BaseModel):
    year: int
    month: int
    day: int
    time: str
    gender: str
    calendar: str
    persona: str

def get_ganji(year):
    chon = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    ji = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    y_idx = (year - 4) % 60
    return f"{chon[y_idx % 10]}{ji[y_idx % 12]}년 ({ji[y_idx % 12]}띠)"

@app.post("/api/fortune")
async def read_fortune(req: SajuRequest):
    final_year, final_month, final_day = req.year, req.month, req.day
    cal_msg = "양력"
    
    if req.calendar == "lunar":
        try:
            calendar = KoreanLunarCalendar()
            calendar.setLunarDate(req.year, req.month, req.day, False)
            final_year = calendar.solarYear
            final_month = calendar.solarMonth
            final_day = calendar.solarDay
            cal_msg = "음력->양력"
        except:
            pass

    ganji = get_ganji(final_year)

    system_role = "너는 용한 점쟁이야."
    if req.persona == "ESTJ":
        system_role = "너는 '호랑이 신령'이야. MBTI는 ESTJ. 공감은 절대 안 해. 팩트로 뼈만 때려. 반말을 쓰고, 아주 엄격하고 무섭게 혼내듯이 말해."
    elif req.persona == "ENFP":
        system_role = "너는 '꽃선녀님'이야. MBTI는 ENFP. 세상 긍정적이고 리액션이 커. '언니가~' 호칭 쓰고 이모티콘 팍팍 써."
    elif req.persona == "INFJ":
        system_role = "너는 '미러 도사'야. MBTI는 INFJ. 깊은 통찰력으로 마음을 꿰뚫어 봐. 차분하고 신비로운 말투를 써."
    elif req.persona == "ENTP":
        system_role = "너는 '괴짜 도깨비'야. MBTI는 ENTP. 장난기가 많고 예측불가능해. 시니컬한 해결책을 던져줘."

    prompt = f"""
    [역할] {system_role}
    [사용자] {final_year}년 {final_month}월 {final_day}일생 ({cal_msg}), {req.gender}, {ganji}, 태어난시간: {req.time}
    [지시] 위 사용자의 올해 운세(재물/연애/직장)를 너의 캐릭터 말투로 찰지게 풀어서 말해줘. 300자 이내, 핵심만 3문단으로.
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return {"result": response.text}
    except Exception as e:
        return {"result": f"신령님이 바쁘시네... 다시 시도해줘. ({str(e)})"}