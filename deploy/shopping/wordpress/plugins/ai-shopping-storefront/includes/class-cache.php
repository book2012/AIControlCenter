<?php

if (!defined('ABSPATH')) {
    exit;
}

final class AI_Shopping_Cache
{
    private int $ttl;

    public function __construct(
        int $ttl = 30
    ) {
        $this->ttl = max(
            1,
            $ttl
        );
    }

    public function get(
        string $key
    ): ?array {
        $value = get_transient(
            $this->normalize_key($key)
        );

        return is_array($value)
            ? $value
            : null;
    }

    public function set(
        string $key,
        array $value
    ): void {
        set_transient(
            $this->normalize_key($key),
            $value,
            $this->ttl
        );
    }

    private function normalize_key(
        string $key
    ): string {
        return 'ai_shop_' . md5($key);
    }
}
