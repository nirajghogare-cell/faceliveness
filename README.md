# 🛡️ LiveGuard AI — Face Liveness & Deepfake Detection

Detect whether a face is **real and live** — not a photo, video replay, or deepfake — using **AWS Rekognition FaceLiveness**.

Built with **Python + FastAPI** backend and a **vanilla HTML/CSS/JS** frontend.

---

## 📐 Architecture

```
Browser (Webcam)
      │
      ▼
FastAPI Server (main.py)
      │
      ├── POST /api/create-session  ──► AWS Rekognition FaceLiveness
      ├── GET  /api/get-result/:id  ──► AWS Rekognition FaceLiveness
      └── GET  /                   ──► static/index.html
```

---

## ⚙️ AWS Setup (Required Before Running)

### 1. Enable AWS Rekognition FaceLiveness

- Make sure your AWS account has access to **Amazon Rekognition** in your target region.
- FaceLiveness is available in: `us-east-1`, `us-west-2`, `eu-west-1`, `ap-southeast-1`, `ap-northeast-1`.

### 2. Create an IAM User

Go to **AWS Console → IAM → Users → Create User**.

Attach this inline policy (minimum permissions):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:CreateFaceLivenessSession",
        "rekognition:GetFaceLivenessSessionResults"
      ],
      "Resource": "*"
    }
  ]
}
```

Generate **Access Key ID** and **Secret Access Key** for this user.

---

## 🚀 Local Setup & Run

### Prerequisites

- Python 3.11+
- pip

### Steps

```bash
# 1. Clone / navigate to project
cd face-liveness-app

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# Edit .env and fill in your AWS credentials + S3 bucket name

# 5. Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 6. Open browser
# http://localhost:8000
```

---

## 🗂️ Project Structure

```
face-liveness-app/
├── main.py                  # FastAPI backend
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .env                     # Your local config (never commit this)
├── .gitignore
├── static/
│   ├── index.html           # Single-page app
│   ├── css/
│   │   └── style.css        # Dark-theme UI
│   └── js/
│       └── app.js           # Camera, API calls, result rendering
└── README.md
```

---

## 🔌 API Reference

### `POST /api/create-session`

Creates a new FaceLiveness session.

**Response:**
```json
{ "session_id": "abc123-..." }
```

### `GET /api/get-result/{session_id}`

Fetches the result of a completed liveness check.

**Response:**
```json
{
  "session_id": "abc123-...",
  "status": "SUCCEEDED",
  "confidence": 97.4,
  "is_live": true,
  "is_deepfake": false,
  "audit_images_count": 4
}
```

| Field | Description |
|---|---|
| `status` | `SUCCEEDED` / `FAILED` / `EXPIRED` / `IN_PROGRESS` |
| `confidence` | 0–100 score from AWS Rekognition |
| `is_live` | `true` if `status == SUCCEEDED` and `confidence >= threshold` |
| `is_deepfake` | `true` if liveness check fails |

### `GET /api/health`

```json
{ "status": "ok", "region": "us-east-1", "threshold": 90.0 }
```

---

## 🔒 Security Notes

- **Never commit `.env`** — it's in `.gitignore`.
- The liveness threshold is set to **90%** by default (AWS recommendation for production).
- No video or images are stored — only session IDs are exchanged with AWS.

---

## 📊 How Deepfake Detection Works

AWS Rekognition FaceLiveness uses computer vision challenges (oval overlay, random movement prompts) and ML models trained on:

- **Photo attacks** — printed photos held in front of camera
- **Video replay attacks** — recorded face played back on a screen
- **3D mask attacks** — physical masks
- **Deepfake / synthetic face attacks** — AI-generated faces

The **confidence score** reflects how likely the captured face is from a live human. Scores below the threshold (default 90) are flagged as potential spoofs.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| AWS SDK | boto3 |
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES2022) |
| AWS Service | Amazon Rekognition FaceLiveness |
