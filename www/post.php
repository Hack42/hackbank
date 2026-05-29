<?php
header('Content-Type: application/json');

function fail_request($message) {
  http_response_code(400);
  echo json_encode(array("done" => 0, "error" => $message));
  exit;
}

function request_string($key, $max_length) {
  if (!isset($_REQUEST[$key]) || !is_string($_REQUEST[$key])) {
    fail_request("Missing ".$key);
  }
  $value = $_REQUEST[$key];
  if ($value === "" || strlen($value) > $max_length) {
    fail_request("Invalid ".$key);
  }
  return $value;
}

require_once(__DIR__."/config.php");

$topic = request_string("topic", 128);
if (!isset($_REQUEST["msg"]) || !is_string($_REQUEST["msg"]) || strlen($_REQUEST["msg"]) > 512) {
  fail_request("Invalid msg");
}
$msg = $_REQUEST["msg"];
if (!preg_match('/^session\/[A-Za-z0-9_-]{1,64}\/input$/', $topic)) {
  fail_request("Invalid topic");
}

require("phpMQTT.php");
use Bluerhinos\phpMQTT;
$mqtt_config = kassa_mqtt_config();
$mqtt = new phpMQTT($mqtt_config["host"], $mqtt_config["port"], "barclient".rand());
if($mqtt->connect()){
  $mqtt->publish("hack42bar/input/".$topic, $msg, 1);
  $mqtt->close();
  echo json_encode(array("done" => 1));
  return ;
}
echo json_encode(array("done" => 0));
return ;

?>
