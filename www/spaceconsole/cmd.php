<?php
header('Content-type: application/json');
function fail_request($message) {
  http_response_code(400);
  echo json_encode(array("message" => $message));
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

$mqtt_host = getenv("MQTT_HOST");
if (empty($mqtt_host)) {
  $mqtt_host = "localhost";
}
$action = request_string("action", 16);
$device = "";
$value = "";
switch ($action) {
  case 'toggle':
    $device = request_string("device", 64);
    if (!preg_match('/^[A-Za-z0-9_-]{1,64}$/', $device)) {
      fail_request("Invalid device");
    }
    break;
  case 'volume':
    $value = request_string("value", 4);
    if (!preg_match('/^[0-9]{1,3}$/', $value) || intval($value) > 100) {
      fail_request("Invalid value");
    }
    break;
  case 'go':
  case 'gdd':
  case 'gd':
  case 'bo':
  case 'bd':
  case 'ko':
  case 'kd':
    break;
  default:
    fail_request("Invalid action");
}

require("../phpMQTT.php");
use Bluerhinos\phpMQTT;
$mqtt = new phpMQTT($mqtt_host, 1883, "barcmnd".rand());

if(!$mqtt->connect()){
  echo json_encode(array("message"=>"MQTT error"));
        exit(1);
}

switch($action) {
  case 'toggle':
    $mqtt->publish("hack42/cmnd/".$device."/POWER","toggle");
    break;
  case 'volume':
    $mqtt->publish("hack42/cmnd/sound/volume",$value);
    break;
  case 'go':
    $mqtt->publish("hack42/stookkelder/gebouw","open");
    $mqtt->publish("hack42/touser/m1","Gebouw gaat open ".date("d/M H:i"),0,1);
    break;
  case 'gdd':
    $mqtt->publish("hack42/stookkelder/gebouw","delay");
    $mqtt->publish("hack42/touser/m1","Gebouw gaat straks dicht ".date("d/M H:i"),0,1);
    break;
  case 'gd':
    $mqtt->publish("hack42/stookkelder/gebouw","close");
    $mqtt->publish("hack42/touser/m1","Gebouw gaat dicht ".date("d/M H:i"),0,1);
    break;
  case 'bo':
    $mqtt->publish("hack42/stookkelder/barakken","open");
    $mqtt->publish("hack42/touser/m1","Barakken gaan open ".date("d/M H:i"),0,1);
    break;
  case 'bd':
    $mqtt->publish("hack42/stookkelder/barakken","close");
    $mqtt->publish("hack42/touser/m1","Barakken gaan dicht ".date("d/M H:i"),0,1);
    break;
  case 'ko':
    $mqtt->publish("hack42/cmnd/kelderpomp/POWER","ON");
    $mqtt->publish("hack42/touser/m1","Kapel gaat aan ".date("d/M H:i"),0,1);
    break;
  case 'kd':
    $mqtt->publish("hack42/cmnd/kelderpomp/POWER","OFF");
    $mqtt->publish("hack42/touser/m1","Kapel gaat uit ".date("d/M H:i"),0,1);
    break;
  default:
    break;
}
?>
