# 🚀 Resolvr — Deployment Guide

This guide walks you through deploying the **Resolvr** application using completely free-tier cloud hosting services:
* **Backend API**: Deployed to [Render](https://render.com/) Web Services (Free Tier) with a persistent storage mount for database integrity.
* **Frontend UI**: Deployed to [Vercel](https://vercel.com/) (Free Tier) with API path rewrites.

---

## 🖥️ 1. Backend Deployment (Render)

Render provides a Free Tier for web applications and allows attaching a persistent disk, which is perfect for maintaining our SQLite and Chroma databases without losing state between service spin-downs.

### Step 1: Create a Render Web Service
1. Log in to [Render Console](https://dashboard.render.com/).
2. Click **New** ➔ **Web Service**.
3. Connect your Resolvr GitHub repository.

### Step 2: Configure Web Service Details
* **Name**: `resolvr-backend`
* **Environment**: `Python`
* **Region**: Choose the region closest to you.
* **Branch**: `master` (or your main development branch)
* **Root Directory**: `backend` (Important: Set this to the `backend` subdirectory)
* **Runtime**: `Python 3`
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port 10000`
* **Instance Type**: `Free`

### Step 3: Attach Persistent Storage (Render Disk)
To prevent your SQLite and Chroma DB stores from resetting every time the Render free-tier container restarts or goes to sleep:
1. In your Render Web Service settings, go to the **Disks** tab.
2. Click **Add Disk**.
3. Configure the disk:
   * **Name**: `resolvr-data`
   * **Mount Path**: `/data` (We will direct our databases to this directory)
   * **Size**: `1 GiB` (Free tier allowance)

### Step 4: Configure Environment Variables
Go to the **Environment** tab and add the following environment variables:
* `DATABASE_URL`: `sqlite:////data/resolvr.db` (Points to the persistent mount path)
* `CHROMA_PERSIST_DIR`: `/data/chroma_store` (Points to the persistent mount path)
* `UPLOAD_DIR`: `/data/uploads` (Points to the persistent mount path)
* `GOOGLE_API_KEY`: `your_gemini_api_key` (Your free-tier Gemini API key from AI Studio)
* `GEMINI_MODEL`: `gemini-2.5-flash` (Defaults to flash)

Click **Save Changes** and Render will trigger the initial deployment. Copy your backend service URL (e.g. `https://resolvr-backend.onrender.com`).

---

## 🎨 2. Frontend Deployment (Vercel)

Vercel hosts Vite/React applications for free and supports seamless rewrites so that backend requests are routed securely and bypass CORS restrictions.

### Step 1: Configure backend proxy link
Open your local [`frontend/vercel.json`](file:///d:/Projects/Resolvr/frontend/vercel.json) file and update the `destination` property of the `/api/:path*` rewrite to point to your live Render backend URL:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://resolvr-backend.onrender.com/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Commit and push this change to your GitHub repository:
```bash
git add frontend/vercel.json
git commit -m "Update vercel proxy destination to live render backend url"
git push
```

### Step 2: Import Project on Vercel
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New** ➔ **Project**.
3. Import your Resolvr GitHub repository.

### Step 3: Configure Build Settings
* **Framework Preset**: `Vite`
* **Root Directory**: `frontend` (Important: Select the `frontend` subdirectory)
* **Build Command**: `pnpm build` or `npm run build`
* **Output Directory**: `dist`

Click **Deploy**. Vercel will install dependencies, compile the production bundles, and set up your application. Once finished, you will receive a public Vercel URL to access your Resolvr client!

---

## 🔍 3. End-to-End Verification

Once both deployments are successful:
1. Open your Vercel frontend URL.
2. Drag and drop a test receipt (e.g. `blurry_receipt.txt` or `text_amounts.xlsx`).
3. Verify that the upload succeeds, progress updates, and the document appears in the document list.
4. Type a query into the chat interface (e.g., *"Reconcile June invoice"*).
5. Open the **Debugger Panel** and verify that you see the real-time agent thoughts streaming down from the Render server.
