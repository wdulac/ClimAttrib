In **{{ year_then|format_year }}**, the probability of such an event was **{{ pF_then|format_prob }}**, corresponding to a return period of **{{ RP_F_then|format_return_period }}**. Without human influence, the same event would have had a probability of **{{ pC_then|format_prob }}**, or a return period of **{{ RP_C_then|format_return_period }}**.
In other words, human activities **{{ has_had }}** made this event
{% if PR_then >= 1 %}
**{{ PR_then|format_PR }}** times **more** likely.
{% else %}
**{{ PR_then_inv|format_PR }}** times **less** likely.
{% endif %}
{% if FAR_then is not none and FAR_then > 0 %}
This implies that **{{ FAR_then|format_FAR }}** of the likelihood of this event can be attributed to climate change.
{% endif %}