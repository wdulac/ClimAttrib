Today in **{{ year_today|format_year }}**, the probability of such an event is **{{ pF_today|format_prob_ci(pF_today_ql, pF_today_qu) }}**,
{% if pF_ratio_now_then >= 1 %}
 **an increase** by a factor of **{{ pF_ratio_now_then|format_PR_ci(pF_ratio_now_then_ql, pF_ratio_now_then_qu) }}**
{% else %}
 **a decrease** by a factor of **{{ pF_ratio_now_then_inv|format_PR_ci(pF_ratio_now_then_inv_ql, pF_ratio_now_then_inv_qu) }}**
{% endif %} compared to **{{ year_then|format_year }}**. Human influence alone now makes an event such as this one
{% if PR_today >= 1 %}
 **{{ PR_today|format_PR_ci(PR_today_ql, PR_today_qu) }}** times **more** likely to occur
{%- else %}
 **{{ PR_today_inv|format_PR_ci(PR_today_inv_ql, PR_today_inv_qu) }}** times **less** likely to occur
{%- endif %}
{%- if FAR_today is not none and FAR_today > 0 %}
, which is equivalent in saying that **{{ FAR_today|format_FAR_ci(FAR_today_ql, FAR_today_qu) }}**
of the likelihood could be attributed to climate change, should it happen again today
{%- endif %}.