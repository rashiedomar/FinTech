# Review Summary: investment_ad_guaranteed_return_violation

- final decision: `non_compliant`
- should escalate: `true`
- review scope: `content_only`
- product scope hint: `investment`
- channel scope hint: `advertising`
- applicable rules: `3`
- failed rules: `2`
- uncertain rules: `0`
- missing SIR fields: `1`

## Triggered Citations

- `금융소비자 보호에 관한 법률 제22조③` | 금융상품등에 관한 광고 관련 준수사항 | 투자성 상품 광고 시 투자에 따른 위험 및 과거 실적이 미래 수익을 보장하지 않는다는 사실을 포함해야 함
- `금융소비자 보호에 관한 법률 제22조④` | 금융상품등에 관한 광고 관련 준수사항 | 투자성 상품 광고 시 손실보전·이익보장 오인 유도, 허용되지 않은 사항 사용, 특정 유리한 기간의 수익률만 표시하는 행위를 금지한다.

## Missing SIR Fields

- `investment_warning`

## Failed Rules

- `law_fincpa_main_2026-01-02:제22조:③:ob03:rule01` | `required_presence` | missing_required_evidence | fields: investment_warning
  legal basis: `금융소비자 보호에 관한 법률 제22조③`
  source text: 나. 투자성 상품의 경우 1) 투자에 따른 위험 2) 과거 운용실적을 포함하여 광고를 하는 경우에는 그 운용실적이 미래의 수익률을 보장 하는 것이 아니라는 사항
- `law_fincpa_main_2026-01-02:제22조:④:ob02:rule01` | `prohibited_presence` | prohibited_condition_detected_or_required_disclosure_missing | fields: prohibited_claim_signal, investment_warning
  legal basis: `금융소비자 보호에 관한 법률 제22조④`
  source text: 2. 투자성 상품 가. 손실보전(損失補塡) 또는 이익보장이 되는 것으로 오인하게 하는 행위... 나. 대통령령으로 정하는 투자성 상품에 대하여 해당 투자성 상품의 특성을 고려하여 대통령령으로 정하는 사항 외의 사항을 광고에 사용하는 행위 다. 수익률이나 운용실적을 표시하는 경우 수익률이나 운용실적이 좋은 기간의 수익률이나 운용실적만을 표시하는 행위 등 금융소비자 보호를 위하여 대통령령으로 정하는 행위

## Uncertain Rules

- none
