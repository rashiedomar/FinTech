# Review Summary: insurance_ad_missing_warning

- final decision: `non_compliant`
- should escalate: `true`
- review scope: `content_only`
- product scope hint: `insurance`
- channel scope hint: `advertising`
- applicable rules: `3`
- failed rules: `2`
- uncertain rules: `0`
- missing SIR fields: `1`

## Triggered Citations

- `금융소비자 보호에 관한 법률 제22조③` | 금융상품등에 관한 광고 관련 준수사항 | 보장성 상품 광고 시 기존 계약 해지 후 신규 계약 체결에 따른 불이익(거부, 보험료 인상, 보장내용 변경 등) 가능성을 포함해야 함
- `금융소비자 보호에 관한 법률 제22조④` | 금융상품등에 관한 광고 관련 준수사항 | 보장성 상품 광고 시 보장 제한, 고액 보장 강조, 보험료 오인 유도, 자동갱신 인상 미고지 등 소비자가 오인할 수 있는 행위를 금지한다.

## Missing SIR Fields

- `insurance_warning`

## Failed Rules

- `law_fincpa_main_2026-01-02:제22조:③:ob02:rule01` | `required_presence` | missing_required_evidence | fields: insurance_warning
  legal basis: `금융소비자 보호에 관한 법률 제22조③`
  source text: 가. 보장성 상품의 경우: 기존에 체결했던 계약을 해지하고 다른 계약을 체결하는 경우에는 계약체결의 거부 또는 보험료 등 금융소비자의 지급비용(이하 이 조에서 “보험료등”이라 한다)이 인상되거나 보장내용이 변경될 수 있다는 사항
- `law_fincpa_main_2026-01-02:제22조:④:ob01:rule01` | `prohibited_presence` | prohibited_condition_detected_or_required_disclosure_missing | fields: insurance_warning
  legal basis: `금융소비자 보호에 관한 법률 제22조④`
  source text: 1. 보장성 상품 가. 보장한도, 보장 제한 조건, 면책사항 또는 감액지급 사항 등을 빠뜨리거나 충분히 고지하지 아니하여 제한 없이 보장을 받을 수 있는 것으로 오인하게 하는 행위 나. 보험금이 큰 특정 내용만을 강조하거나 고액 보장 사례 등을 소개하여 보장내용이 큰 것으로 오인하게 하는 행위 다. 보험료를 일(日) 단위로 표시하거나 보험료의 산출기준을 불충분하게 설명하는 등 보험료등이 저렴한 것으로 오인하게 하는 행위 라. 만기 시 자동갱신되는 보장성 상품의 경우 갱신 시 보험료등이 인상될 수 있음을 금융소비자가 인지할 수 있도록 충분히 고지하지 아니하는 행위 마. 금리 및 투자실적에 따라 만기환급금이 변동될 수 있는 보장성 상품의 경우 만기환급금이 보장성 상품의 만기일에 확정적으로 지급되는 것으로 오인하게 하는 행위 등 금융소비자 보호를 위하여 대통령령으로 정하는 행위

## Uncertain Rules

- none
