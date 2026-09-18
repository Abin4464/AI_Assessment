from data_loader import load_tickets
from nlq_engine import ask_question

SAMPLE_QUESTIONS = [
    "How many tickets are currently open?",
    "Which agent resolved the most tickets this month?",
    "Show me all Critical tickets not resolved within 12 hours.",
    "What is the average customer rating for Technical category tickets?",
]

if __name__ == "__main__":
    df = load_tickets()
 
    for question in SAMPLE_QUESTIONS:
        print("=" * 70)
        print("Q:", question)
        result = ask_question(df, question)
 
        if result["success"]:
            print("Generated code:", result["generated_code"])
            print("Answer:", result["answer"])
        else:
            print("ERROR:", result["error"])
            if "generated_code" in result:
                print("Generated code was:", result["generated_code"])
        print()