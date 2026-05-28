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

echo "PHP file tests passed\n";
