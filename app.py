from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from deepface import DeepFace
import shutil, os, smtplib
from email.message import EmailMessage
from email.utils import make_msgid
import matplotlib.pyplot as plt

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def map_race_to_country(race_result):
    mapping = {
        "asian": "Japan, China, Korea",
        "white": "USA, Germany, Netherlands",
        "middle eastern": "Iran, Saudi Arabia, Turkey",
        "latino hispanic": "Mexico, Brazil, Argentina",
        "black": "Nigeria, Kenya, Ethiopia"
    }
    return mapping.get(race_result, "Unknown")

def create_pie_chart(race_dict):
    labels = list(race_dict.keys())
    sizes = list(race_dict.values())
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.tight_layout()
    plt.savefig("race_chart.png")
    plt.close()

def send_email(to_email, result):
    dominant_race = result["dominant_race"]
    countries = map_race_to_country(dominant_race)
    race_data = result["race"]
    create_pie_chart(race_data)

    msg = EmailMessage()
    msg["Subject"] = "AI Nationality Detection Result"
    msg["From"] = "h.shojaei2024@gmail.com"
    msg["To"] = to_email

    photo_cid = make_msgid(domain="xyz.com")
    chart_cid = make_msgid(domain="xyz.com")

    html = f"""    <html>
      <body style="font-family:sans-serif;">
        <h2 style="color:#333;">🌍 AI Nationality Detection Result</h2>
        <p><strong>Dominant Race:</strong> <span style="color:#007BFF;">{dominant_race.title()}</span></p>
        <p><strong>Suggested Countries:</strong> {countries}</p>
        <img src="cid:{photo_cid[1:-1]}" width="200" style="margin-top:10px; border-radius:10px;"><br><br>
        <img src="cid:{chart_cid[1:-1]}" width="300">
        <p style="font-size:12px;color:#888;">Thank you for using our AI Service ✨</p>
      </body>
    </html>
    """.strip()

    msg.add_alternative(html, subtype="html")

    with open("temp.jpg", "rb") as f:
        msg.get_payload()[0].add_related(f.read(), "image", "jpeg", cid=photo_cid)

    with open("race_chart.png", "rb") as f:
        msg.get_payload()[0].add_related(f.read(), "image", "png", cid=chart_cid)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("h.shojaei2024@gmail.com", "xsne fmdu vjhy goji")
        smtp.send_message(msg)

@app.post("/analyze/")
async def analyze_image(file: UploadFile = File(...), email: str = Form(...)):
    with open("temp.jpg", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = DeepFace.analyze(img_path="temp.jpg", actions=["race"], enforce_detection=False)[0]
        send_email(email, result)
        os.remove("temp.jpg")
        os.remove("race_chart.png")
        return {"status": "success", "message": "Beautiful result sent to your email."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})