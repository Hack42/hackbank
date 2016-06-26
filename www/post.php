<?php
header('Content-Type: application/json');
require("phpMQTT.php");
$mqtt = new phpMQTT("localhost", 1883, "barclient".rand());
if($mqtt->connect()){
  $mqtt->publish("hack42bar/input/".$_REQUEST['topic'],$_REQUEST['msg'],1);
  $mqtt->close();
  echo json_encode(array("done" => 1));
  return ;
}
echo json_encode(array("done" => 0));
return ;

?>
