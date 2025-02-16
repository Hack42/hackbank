<?php
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
@ini_set('zlib.output_compression',0);
@ini_set('implicit_flush',1);
@ob_end_clean();
set_time_limit(0);
function procmsg($topic,$msg){
//  $msg=substr($msg,2);
  echo "data: ".json_encode(array($topic,$msg))."\n\n";
  @flush();
  @ob_flush();
}

##
require("phpMQTT.php");

$mqtt_host = $_ENV["MQTT_HOST"];
if (empty($mqtt_host)) {
  $mqtt_host = "localhost";
}
use Bluerhinos\phpMQTT;
$mqtt = new phpMQTT($mqtt_host, 1883, "barclient".rand());
if(!$mqtt->connect()){
	exit(1);
}
$topics['hack42bar/output/session/'.$_REQUEST['session'].'/#'] = array("qos"=>0, "function"=>"procmsg");
$mqtt->subscribe($topics,0);
echo "data: ".json_encode(array("startup","1"))."\n\n";
@flush();
@ob_flush();
while($mqtt->proc()){
		
}
echo "data: closed\n\n";
$mqtt->close();

?>
