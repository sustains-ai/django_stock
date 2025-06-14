# ai_agent.py

from openai import OpenAI
from .models import Portfolio, HistoricalStockData
from .risk_analysis import perform_risk_analysis, calculate_risk_measures
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def get_portfolio_returns_df(portfolio: Portfolio) -> pd.DataFrame:
    """Builds a DataFrame of adjusted close prices from historical stock data."""
    data = HistoricalStockData.objects.filter(
        portfolio=portfolio).order_by("date")
    symbols = list(set(data.values_list("symbol", flat=True)))
    if not symbols:
        return pd.DataFrame()

    df = pd.DataFrame()
    for symbol in symbols:
        symbol_data = data.filter(
            symbol=symbol).values(
            "date",
            "adjusted_close")
        if symbol_data:
            df_symbol = pd.DataFrame.from_records(symbol_data)
            df_symbol.set_index("date", inplace=True)
            df_symbol.rename(columns={"adjusted_close": symbol}, inplace=True)
            df = pd.concat([df, df_symbol], axis=1)

    return df.pct_change().dropna()


def portfolio_risk_agent(portfolio_id: int, question: str) -> str:
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        returns_df = get_portfolio_returns_df(portfolio)

        if returns_df.empty:
            return "No sufficient historical data available for risk analysis."

        optimal_weights = perform_risk_analysis(returns_df)
        risk_measures = calculate_risk_measures(
            returns_df, list(returns_df.columns))

        context = f"""
        You are a portfolio risk analysis agent.
        Portfolio: {portfolio.name}
        Optimized weights (Mean-Variance): {optimal_weights['mean_variance']}
        Risk measures per stock: {risk_measures}
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    f"{context.strip()}\n"
                    "When responding, always use 4 plain text bullet points and avoid bold, italic, or any markdown and keep all the bullet points in different lines and adequate space."
                    " Your job is to help analyze the portfolio using the provided context. Be clear and structured."
                )},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Agent error: {str(e)}"
