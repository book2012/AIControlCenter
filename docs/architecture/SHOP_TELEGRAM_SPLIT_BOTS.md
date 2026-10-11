# Telegram environment separation

DEV: papachichi_bot, independent poller, cursor and lock. The separate consumer forwards only authenticated authorized private-chat messages through the DEV Unix socket. Update IDs are mapped by adding 2^60 to avoid historical shared-bot collisions. Ambiguous commands are not replayed. DEV outbound notifications use the same DEV token after activation.

PROD: mommychichi_bot, existing cursor and business release lineage retained. split_bot_mode disables embedded DEV composition and forwarding, with DEV-prefixed commands rejected. No stock, payment, order or SMS mutation is part of migration.

Activation preserves backups, verifies bot identity/operator binding, stops the shared forwarding path and switches DEV token before starting the new consumer. Revert launch/config pins without resetting cursors.

## Activation checkpoint 2026-10-12 08:49 KST
Both bot consumers activated with distinct tokens/cursors/locks. User confirmed DEV connection message receipt. DEV API retains 3433ccc and QWEN_DEV; DEV consumer pin 1eb15cf. PROD API cc464bf split mode RUNNING; prior presentation pin retained. SMS remains disabled; original dirty tree preserved. Private config and launch manifests backed up with suffix 20261012-0850. New command acknowledgement test remains a user acceptance step.
