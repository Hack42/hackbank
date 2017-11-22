<?php
header('Content-Type: application/json');
require("phpMQTT.php");

$mqtt_host = $_ENV["MQTT_HOST"];
if (empty($mqtt_host)) {
  $mqtt_host = "localhost";
}

$mqtt = new phpMQTT($mqtt_host, 1883, "barclient".rand());
if($mqtt->connect()){
  $mqtt->publish("hack42bar/input/".$_REQUEST['topic'],$_REQUEST['msg'],1);
  $mqtt->close();
  echo json_encode(array("done" => 1));
  return ;
}
echo json_encode(array("done" => 0));
return ;

?>
