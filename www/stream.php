<?php
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');
@ini_set('zlib.output_compression',0);
@ini_set('implicit_flush',1);
@ob_end_clean();
set_time_limit(0);
function fail_request($message) {
  http_response_code(400);
  echo "event: error\n";
  echo "data: ".json_encode(array("error" => $message))."\n\n";
  exit;
}

function request_session() {
  if (!isset($_REQUEST['session']) || !is_string($_REQUEST['session'])) {
    fail_request("Missing session");
  }
  $session = $_REQUEST['session'];
  if (!preg_match('/^[A-Za-z0-9_-]{1,64}$/', $session)) {
    fail_request("Invalid session");
  }
  return $session;
}

function procmsg($topic,$msg){
//  $msg=substr($msg,2);
  echo "data: ".json_encode(array($topic,$msg))."\n\n";
  @flush();
  @ob_flush();
}

##
$mqtt_host = getenv("MQTT_HOST");
if (empty($mqtt_host)) {
  $mqtt_host = "localhost";
}
$session = request_session();
require("phpMQTT.php");
use Bluerhinos\phpMQTT;
$mqtt = new phpMQTT($mqtt_host, 1883, "barclient".rand());
if(!$mqtt->connect()){
	exit(1);
}
$topics['hack42bar/output/session/'.$session.'/#'] = array("qos"=>0, "function"=>"procmsg");
$mqtt->subscribe($topics,0);
echo "retry: 1000\n";
echo "data: ".json_encode(array("startup","1"))."\n\n";
@flush();
@ob_flush();
$last_ping = time();
while($mqtt->proc()){
  if (connection_aborted()) {
    break;
  }
  if ($last_ping < time() - 15) {
    echo ": keepalive\n\n";
    @flush();
    @ob_flush();
    $last_ping = time();
  }
}
echo ": closed\n\n";
$mqtt->close();

?>
