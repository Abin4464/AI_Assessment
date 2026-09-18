from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd

from data_loader import load_tickets
from nlq_engine import ask_question
from anomaly_detector import get_all_anomalies

app = FastAPI(title="Support Ticket AI System")

_tickets_df = load_tickets()

class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health_check():
    """Simple endpoint to confirm the server is up and the data loaded."""
    return {"status": "ok", "tickets_loaded": len(_tickets_df)}


@app.post("/query")
def query_tickets(request: QuestionRequest):
    """
    Accepts a natural language question and returns the AI-generated
    answer. Example request body: {"question": "How many tickets are open?"}
    """
    result = ask_question(_tickets_df, request.question)

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["error"])

    answer = result["answer"]
    if isinstance(answer, pd.DataFrame):
        answer = answer.to_dict(orient="records")
    elif isinstance(answer, pd.Series):
        answer = answer.to_dict()
    elif hasattr(answer, "item"):  # numpy scalar types (e.g. numpy.float64)
        answer = answer.item()

    return {
        "question": request.question,
        "answer": answer,
        "generated_code": result["generated_code"],
    }


@app.get("/anomalies")
def anomalies():
    """Returns both categories of detected anomalies."""
    return get_all_anomalies(_tickets_df)