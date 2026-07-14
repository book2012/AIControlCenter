# Shadow Observation

## Purpose

The Shadow Observation service validates the Mac
AIControlCenter Control Plane before production cutover.

The observer is read-only and runs every five minutes.

## Service

- Label:
  `com.aicontrolcenter.api.shadow.observer`
- Application user:
  `kyouhan`
- Interval:
  `300 seconds`
- Observation data:
  `/var/log/aicontrolcenter/shadow-observation.jsonl`
- Observer stdout:
  `/var/log/aicontrolcenter/shadow-observer.stdout.log`
- Observer stderr:
  `/var/log/aicontrolcenter/shadow-observer.stderr.log`

## Collected Signals

- Git working tree state
- Git commit
- Runtime commit
- Health HTTP status
- Write-protection HTTP status
- Listener address
- Process user
- PID
- CPU percentage
- RSS memory
- Daemon log size

## Production Gate

The observation window is complete when:

- duration is at least 23.5 hours
- at least 276 samples exist
- success ratio is at least 99.5%
- no listener exposure is detected
- no root application process is detected
- the final sample passes

Observation completion does not automatically authorize
production cutover.
