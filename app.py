from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from typing import List, Optional
import logging

from perplexity_service import PerplexityService

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Medication Recommender")

# Set up static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Perplexity service
perplexity_service = PerplexityService()

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the homepage"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.post("/recommend", response_class=HTMLResponse)
async def recommend_medication(
    request: Request,
    symptoms: str = Form(...),
    form_type: str = Form(...)
):
    """Process medication recommendation request"""
    try:
        # Split and clean symptoms
        symptom_list = [s.strip() for s in symptoms.split(',') if s.strip()]
        
        if not symptom_list:
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request,
                    "error": "Please enter at least one symptom."
                }
            )
        
        # Validate medication form type
        if form_type not in ["알약", "물약"]:
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request,
                    "error": "Please select a valid medication form (알약 or 물약)."
                }
            )
        
        # Get medication recommendations via Perplexity API
        medications = perplexity_service.get_medication_recommendations(symptom_list, form_type)
        
        if not medications:
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request,
                    "error": "Failed to get medication recommendations. Please try again."
                }
            )
        
        # Render results page
        return templates.TemplateResponse(
            "results.html", 
            {
                "request": request,
                "medications": medications,
                "symptoms": symptoms,
                "form_type": form_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error in medication recommendation: {e}")
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "error": "An error occurred while processing your request. Please try again."
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Server startup code
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)