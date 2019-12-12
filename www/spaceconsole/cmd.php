<?php
header('Content-type: application/json');
require("phpMQTT.php");
$mqtt = new phpMQTT("192.168.142.66", 1883, "barcmnd".rand());



if(!$mqtt->connect()){
  echo json_encode(array("message"=>"MQTT error"));
        exit(1);
}


switch($_REQUEST["action"]) {
  case 'toggle':
    $mqtt->publish("hack42/cmnd/".$_REQUEST["device"]."/POWER","toggle");
  case 'volume':
    $mqtt->publish("hack42/cmnd/sound/volume",$_REQUEST["value"]);
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
    echo json_encode(array("message"=>"Wrong password"));
    break;
}
?>
