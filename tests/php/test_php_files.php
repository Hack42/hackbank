<?php

declare(strict_types=1);

$root = dirname(__DIR__, 2);

function assert_true(bool $condition, string $message): void
{
    if (!$condition) {
        fwrite(STDERR, $message . PHP_EOL);
        exit(1);
    }
}

function all_php_files(string $directory): array
{
    $files = [];
    $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($directory));
    foreach ($iterator as $file) {
        if ($file->isFile() && $file->getExtension() === 'php') {
            $files[] = $file->getPathname();
        }
    }
    sort($files);
    return $files;
}

foreach (all_php_files($root . '/www') as $file) {
    $command = escapeshellcmd(PHP_BINARY) . ' -l ' . escapeshellarg($file);
    exec($command, $output, $status);
    assert_true($status === 0, implode(PHP_EOL, $output));
}

assert_true(
    !file_exists($root . '/www/spaceconsole/phpMQTT.php'),
    'spaceconsole must use the shared www/phpMQTT.php client'
);

foreach (glob($root . '/www/spaceconsole/*.php') as $file) {
    $source = file_get_contents($file);
    assert_true(
        $source === false || !str_contains($source, 'require("phpMQTT.php")'),
        basename($file) . ' must not load a local phpMQTT duplicate'
    );
}

require_once $root . '/www/config.php';

$config_file = tempnam(sys_get_temp_dir(), 'kassa-config-');
assert_true($config_file !== false, 'could not create temporary config file');
file_put_contents($config_file, "mqtt:\n  host: mqtt.example.test\n  port: 1884\n");
putenv("MQTT_HOST");
putenv("MQTT_PORT");
assert_true(
    kassa_config_get(array("mqtt", "host"), null, $config_file) === "mqtt.example.test",
    'PHP config should read mqtt.host from config.yaml'
);
assert_true(
    kassa_mqtt_config($config_file) === array("host" => "mqtt.example.test", "port" => 1884),
    'PHP MQTT config should use config.yaml when env vars are absent'
);

putenv("MQTT_HOST=127.0.0.1");
putenv("MQTT_PORT=1885");
assert_true(
    kassa_mqtt_config($config_file) === array("host" => "127.0.0.1", "port" => 1885),
    'MQTT_HOST and MQTT_PORT should override config.yaml'
);
putenv("MQTT_HOST");
putenv("MQTT_PORT");
unlink($config_file);

echo "PHP file tests passed\n";
