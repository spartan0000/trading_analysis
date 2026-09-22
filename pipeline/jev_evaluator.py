import os
import logging

from typesafe_sdk import TypeSafeClient, AsyncTypeSafeClient, Choice, Noul, Score

def evaluate_signal(signal, regime):
    """
    Soft judgement layer using Jev
    Called after the hard filters pass.
    Returns (should_trade, response) — response is the SystemOneResponse, or None
    if the evaluation itself failed (in which case should_trade defaults to True).
    """

    try:
        with TypeSafeClient() as client:
           response = client.system_one(
               state={
                    "ticker": signal['ticker'],
                    "company": signal['company'],
                    "insider_name": signal['insider_name'],
                    "officer_title": signal.get('officer_title', 'Unknown'),
                    "is_ceo": bool(signal['is_ceo']),
                    "is_officer": bool(signal['is_officer']),
                    "is_director": bool(signal['is_director']),
                    "purchase_value": float(signal['purchase_value']),
                    "pct_added": float(signal['pct_added']),
                    "direct_indirect": signal['DirectIndirect'],
                    "filing_lag": int(signal['filing_lag']),
                    "market_regime": regime,
                    "is_first_purchase": bool(signal.get('is_first_purchase', False))
                },
                questions={
                    "signal_quality": Choice(
                        instructions="What is the overall quality of this insider trading signal?",
                        criteria={
                            "strong": "High conviction purchase with meaningful stake increase by senior insider",
                            "moderate": "Reasonable signal but some characteristics are weak",
                            "weak": "Signal lacks conviction or has concerning characteristics",
                            "noise": "Administrative or routine purchase with no informational value"
                        }
                    ),
                    "genuine_conviction": Noul(
                        instructions="Does this purchase represent genuine insider conviction rather than routine accumulation or administrative buying?"
                    ),
                    "regime_appropriate": Noul(
                        instructions="Is the current market regime appropriate for acting on this insider signal?"
                    ),
                    "alpha_potential": Score(
                        instructions="How likely is this signal to generate positive alpha above SPY?",
                        criteria=[
                            "very unlikely",
                            "unlikely", 
                            "neutral",
                            "likely",
                            "very likely"
                        ]
                    ),
                    "matches_target_profile": Noul(
                        instructions="Does this signal match our target profile: indirect ownership, meaningful stake increase, senior insider, timely filing, bull or neutral_bull regime?"
                    )
                }
            )
        # Extract results using correct response structure
        signal_quality = response.choices["signal_quality"].choice
        signal_confidence = response.choices["signal_quality"].confidence

        genuine_conviction = response.nouls["genuine_conviction"].noul
        regime_appropriate = response.nouls["regime_appropriate"].noul
        matches_profile = response.nouls["matches_target_profile"].noul

        alpha_potential = response.scores["alpha_potential"].score
        signal_probs = response.choices["signal_quality"].probabilities

        logging.info(f"""
        Jev evaluation: {signal['ticker']}
            Signal quality:  {signal_quality} ({signal_confidence:.0%})
            Signal probabilities: {signal_probs}
            Conviction:      {genuine_conviction:.2f}
            Regime fit:      {regime_appropriate:.2f}
            Alpha potential: {alpha_potential}
            Matches profile: {matches_profile:.2f}
        """.strip())

        # Decision logic
        should_trade = all([
            signal_quality in ['strong', 'moderate'],
            signal_confidence > 0.75,
            genuine_conviction > 0.7,
            alpha_potential in ['likely', 'very likely'],
            matches_profile > 0.7
        ])

        return should_trade, response
    except Exception as e:
        # Fail open by design — a Jev outage shouldn't block trading on the hard
        # rules alone — but log enough to tell a real bug apart from a transient
        # API failure (timeout, rate limit, auth) next time this fires.
        logging.error(
            f"Jev evaluation failed for {signal['ticker']} ({type(e).__name__}): {e}",
            exc_info=True
        )
        return True, None