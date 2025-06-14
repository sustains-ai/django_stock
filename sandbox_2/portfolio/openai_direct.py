from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client
client = OpenAI()


def ask_openai(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a portfolio analysis assistant. Respond accurately."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content.strip()


# Test run
if __name__ == "__main__":
    q1 = "What is the Sharpe ratio of a portfolio with return 12% and std deviation 4%?"
    print("Q:", q1)
    print("A:", ask_openai(q1))
