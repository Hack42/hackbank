<?php
declare(strict_types=1);

header('Content-Type: application/json');
header('Cache-Control: no-store');

function audio_error(int $status, string $message): never {
    http_response_code($status);
    echo json_encode(['error' => $message]);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];
if (!in_array($method, ['GET', 'POST'], true)) {
    audio_error(405, 'Method not allowed');
}
$body = '';
if ($method === 'POST') {
    if (strtolower(trim(explode(';', $_SERVER['CONTENT_TYPE'] ?? '')[0])) !== 'application/json') {
        audio_error(415, 'JSON required');
    }
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    $origin_parts = $origin !== '' ? parse_url($origin) : [];
    if ($origin !== '') {
        if (!is_array($origin_parts) || !isset($origin_parts['host'])) {
            audio_error(403, 'Invalid origin');
        }
        $authority = $origin_parts['host'] . (isset($origin_parts['port']) ? ':' . $origin_parts['port'] : '');
        if (strcasecmp($authority, $_SERVER['HTTP_HOST'] ?? '') !== 0) {
            audio_error(403, 'Invalid origin');
        }
    }
    $body = file_get_contents('php://input', false, null, 0, 257);
    $request = json_decode($body ?: '', true);
    if (strlen($body ?: '') > 256 || !is_array($request) || count($request) !== 2
        || !in_array($request['channel'] ?? null, ['pos', 'space'], true)
        || !isset($request['volume']) || !is_int($request['volume'])
        || $request['volume'] < 0 || $request['volume'] > 100) {
        audio_error(400, 'Invalid volume request');
    }
    $body = json_encode($request);
}

$path = getenv('KASSA_AUDIO_SOCKET') ?: '/run/hackbank-audio/control.sock';
$socket = @stream_socket_client('unix://' . $path, $error_code, $error_message, 1);
if ($socket === false) {
    audio_error(503, 'Audio controls are unavailable');
}
stream_set_timeout($socket, 20);
$message = $method . " /volume HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n";
if ($method === 'POST') {
    $message .= "Content-Type: application/json\r\nContent-Length: " . strlen($body) . "\r\n";
}
fwrite($socket, $message . "\r\n" . $body);
$response = stream_get_contents($socket, 16384);
fclose($socket);
if ($response === false || !preg_match('/^HTTP\/1\.[01] (\d{3}) /', $response, $matches)) {
    audio_error(503, 'Audio controls are unavailable');
}
$parts = explode("\r\n\r\n", $response, 2);
$payload = isset($parts[1]) ? json_decode($parts[1], true) : null;
if (!is_array($payload)) {
    audio_error(503, 'Audio controls are unavailable');
}
http_response_code((int) $matches[1]);
echo json_encode($payload);
