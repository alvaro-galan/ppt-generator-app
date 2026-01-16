# Voice-to-Presentation Platform

A complete platform to generate PowerPoint presentations from audio input using Google Gemini 1.5 Flash.

## Features

- **Web Interface**: Record or upload audio files.
- **WhatsApp Integration**: Send audio notes to a WhatsApp bot to receive a PPTX file.
- **AI Processing**: Uses Gemini 1.5 Flash for multimodal analysis.
- **Background Processing**: Redis + Celery for handling heavy tasks.

## Project Structure

- `/backend`: FastAPI application, Celery worker, and AI logic.
- `/frontend`: React + Vite + TypeScript application with Tailwind CSS.
- `docker-compose.yml`: Orchestration for local development and deployment.

## Prerequisites

- Docker & Docker Compose
- Google Gemini API Key
- Meta for Developers Account (for WhatsApp API)

## Setup & Run Locally

1. **Clone the repository**

2. **Environment Variables**
   Create a `.env` file in the `backend` directory (or set them in your environment/docker-compose):
   ```
   GOOGLE_API_KEY=your_key
   WHATSAPP_VERIFY_TOKEN=your_token
   WHATSAPP_API_TOKEN=your_token
   WHATSAPP_PHONE_NUMBER_ID=your_id
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs

## Deployment on Dokploy

1. **VPS Setup**: Ensure your Hostinger VPS has Docker and Dokploy installed.
2. **Create Project**: In Dokploy, create a new project.
3. **Services**:
   - **Database**: Add a PostgreSQL service.
   - **Redis**: Add a Redis service.
   - **Backend**: Add an Application service pointed to the `/backend` folder (or use Dockerfile). Set environment variables.
   - **Worker**: Add another Application service (or use the same image with a different start command: `celery -A tasks worker --loglevel=info`).
   - **Frontend**: Add an Application service pointed to the `/frontend` folder (Dockerfile build).

   Alternatively, you can use the `docker-compose.yml` stack deployment feature in Dokploy if supported, or manually deploy the stack via SSH.

## WhatsApp Configuration

1. Go to the Meta Developers Portal.
2. Set up the Webhook URL to `https://your-backend-domain.com/webhook`.
3. Verify the token matches `WHATSAPP_VERIFY_TOKEN`.
4. Subscribe to `messages` events.

## Tech Stack

- **Frontend**: React, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python, FastAPI, Celery
- **AI**: Google Gemini 1.5 Flash
- **Database**: PostgreSQL (Provisioned but not currently used in MVP logic), Redis (Queue)
