# Telegram environment separation

DEV: papachichi_bot, independent poller, cursor and lock. The separate consumer forwards only authenticated authorized private-chat messages through the DEV Unix socket. Update IDs are mapped by adding 2^60 to avoid historical shared-bot collisions. Ambiguous commands are not replayed. DEV outbound notifications use the same DEV token after activation.

PROD: mommychichi_bot, existing cursor and business release lineage retained. split_bot_mode disables embedded DEV composition and forwarding, with DEV-prefixed commands rejected. No stock, payment, order or SMS mutation is part of migration.

Activation preserves backups, verifies bot identity/operator binding, stops the shared forwarding path and switches DEV token before starting the new consumer. Revert launch/config pins without resetting cursors.
