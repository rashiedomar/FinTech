# Review Summary: deposit_ad_missing_disclaimer

- final decision: `non_compliant`
- should escalate: `true`
- review scope: `content_only`
- product scope hint: `deposit`
- channel scope hint: `advertising`
- applicable rules: `3`
- failed rules: `2`
- uncertain rules: `0`
- missing SIR fields: `1`

## Triggered Citations

- `금융소비자 보호에 관한 법률 제22조③` | 금융상품등에 관한 광고 관련 준수사항 | 예금성 상품 광고 시 만기지급금 등을 예시하는 경우 해당 예시가 미래 수익을 보장하지 않는다는 사실을 포함해야 함 (대통령령으로 정하는 변동금리 상품에 한함)
- `금융소비자 보호에 관한 법률 제22조④` | 금융상품등에 관한 광고 관련 준수사항 | 예금성 상품 광고 시 이자율 범위·산정방법 등을 불명확하게 표시하여 오인을 유도하거나 유리한 기간의 수익률만 표시하는 행위를 금지한다.

## Missing SIR Fields

- `deposit_disclaimer`

## Failed Rules

- `law_fincpa_main_2026-01-02:제22조:③:ob04:rule01` | `required_presence` | missing_required_evidence | fields: deposit_disclaimer
  legal basis: `금융소비자 보호에 관한 법률 제22조③`
  source text: 다. 예금성 상품의 경우: 만기지급금 등을 예시하여 광고하는 경우에는 해당 예시된 지급금 등이 미래의 수익을 보장하는 것이 아니라는 사항(만기 시 지급금이 변동하는 예금성 상 품으로서 대통령령으로 정하는 금융상품의 경우에 한정한다)
- `law_fincpa_main_2026-01-02:제22조:④:ob03:rule01` | `prohibited_presence` | prohibited_condition_detected_or_required_disclosure_missing | fields: prohibited_claim_signal, deposit_disclaimer
  legal basis: `금융소비자 보호에 관한 법률 제22조④`
  source text: 3. 예금성 상품 가. 이자율의 범위ㆍ산정방법, 이자의 지급ㆍ부과 시기 및 부수적 혜택ㆍ비용을 명확히 표시하지 아니하여 금융소비자가 오인하게 하는 행위 나. 수익률이나 운용실적을 표시하는 경우 수익률이나 운용실적이 좋은 기간의 것만을 표시하는 행위 등 금융소비자 보호를 위하여 대통령령으로 정하는 행위

## Uncertain Rules

- none
