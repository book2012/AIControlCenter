# M3-A4B2B Permit Approval Responsibility Matrix

| Responsibility | Required future actor | M3-A4B2B1A state |
|---|---|---|
| Request controlled non-production issuance | Explicit requester | NOT PROVIDED |
| Operate the Mac Control Plane | Explicit Mac operator | NOT PROVIDED |
| Independently approve | Named approver distinct from operator | NOT PROVIDED |
| Prevent requester/operator self-approval | Control Plane policy | ENFORCED |
| Acknowledge branch, commit, targets, schemas and plans | Operator and approver | NOT PROVIDED |
| Acknowledge every restriction, including 427 warnings | Operator and approver | NOT PROVIDED |
| Issue and record the M3-A4B1 permit | Future M3-A4B2B1B flow | NOT PERFORMED |
| Claim and execute bootstrap | Future separately authorized flow | NOT PERFORMED |
| Authorize production | Separate production gate | NOT_AUTHORIZED |

Anonymous, test, placeholder and example identities are prohibited. Ubuntu has
no authorization, issuance, claim, execution or Control Plane responsibility.
