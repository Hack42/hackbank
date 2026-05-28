<?php

declare(strict_types=1);

function kassa_default_config(): array
{
    return array(
        "mqtt" => array(
            "host" => "localhost",
            "port" => 1883,
        ),
    );
}

function kassa_merge_config(array $base, array $override): array
{
    foreach ($override as $key => $value) {
        if (is_array($value) && isset($base[$key]) && is_array($base[$key])) {
            $base[$key] = kassa_merge_config($base[$key], $value);
        } else {
            $base[$key] = $value;
        }
    }
    return $base;
}

function kassa_set_nested_config(array &$config, array $path, mixed $value): void
{
    $target =& $config;
    $last = array_pop($path);
    foreach ($path as $key) {
        if (!isset($target[$key]) || !is_array($target[$key])) {
            $target[$key] = array();
        }
        $target =& $target[$key];
    }
    $target[$last] = $value;
}

function kassa_parse_yaml_scalar(string $value): mixed
{
    $value = trim($value);
    if ($value === "") {
        return "";
    }
    if (preg_match('/^-?[0-9]+$/', $value)) {
        return intval($value);
    }
    if ($value === "true") {
        return true;
    }
    if ($value === "false") {
        return false;
    }
    return trim($value, "\"'");
}

function kassa_parse_simple_yaml(string $content): array
{
    $config = array();
    $path_by_level = array();
    foreach (preg_split('/\r?\n/', $content) as $line) {
        if (trim($line) === "" || str_starts_with(trim($line), "#")) {
            continue;
        }
        if (!preg_match('/^(\s*)([A-Za-z0-9_-]+):(?:\s*(.*))?$/', $line, $matches)) {
            continue;
        }
        $level = intdiv(strlen($matches[1]), 2);
        $key = $matches[2];
        $raw_value = $matches[3] ?? "";
        $path = array_slice($path_by_level, 0, $level);
        $path[] = $key;
        $path_by_level[$level] = $key;
        foreach (array_keys($path_by_level) as $existing_level) {
            if ($existing_level > $level) {
                unset($path_by_level[$existing_level]);
            }
        }
        kassa_set_nested_config(
            $config,
            $path,
            trim($raw_value) === "" ? array() : kassa_parse_yaml_scalar($raw_value)
        );
    }
    return $config;
}

function kassa_config_load(?string $path = null): array
{
    $path = $path ?: getenv("KASSA_CONFIG") ?: dirname(__DIR__) . "/config.yaml";
    if (!is_file($path)) {
        return kassa_default_config();
    }
    $content = file_get_contents($path);
    if ($content === false) {
        return kassa_default_config();
    }
    return kassa_merge_config(kassa_default_config(), kassa_parse_simple_yaml($content));
}

function kassa_config_get(array $keys, mixed $default = null, ?string $path = null): mixed
{
    $value = kassa_config_load($path);
    foreach ($keys as $key) {
        if (!is_array($value) || !array_key_exists($key, $value)) {
            return $default;
        }
        $value = $value[$key];
    }
    return $value;
}

function kassa_mqtt_config(?string $path = null): array
{
    $host = getenv("MQTT_HOST");
    if ($host === false || $host === "") {
        $host = kassa_config_get(array("mqtt", "host"), "localhost", $path);
    }
    $port = getenv("MQTT_PORT");
    if ($port === false || $port === "") {
        $port = kassa_config_get(array("mqtt", "port"), 1883, $path);
    }
    return array(
        "host" => $host,
        "port" => intval($port),
    );
}
