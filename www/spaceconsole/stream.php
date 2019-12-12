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
$mqtt = new phpMQTT("192.168.142.66", 1883, "barclient".rand());
if(!$mqtt->connect()){
	exit(1);
}
$topics['hack42/stat/+/POWER'] = array("qos"=>0, "function"=>"procmsg");
$topics['hack42/tele/#'] = array("qos"=>0, "function"=>"procmsg");
$topics['hack42/state'] = array("qos"=>0, "function"=>"procmsg");
$topics['hack42/stookkelder/+'] = array("qos"=>0, "function"=>"procmsg");
$topics['hack42/sensors/#'] = array("qos"=>0, "function"=>"procmsg");
$topics['hack42/sound/volume'] = array("qos"=>0, "function"=>"procmsg");
#$topics['hack42/sensors/dht11/+/humid'] = array("qos"=>0, "function"=>"procmsg");
$mqtt->subscribe($topics,0);
echo "data: ".json_encode(array("startup","1"))."\n\n";
@flush();
@ob_flush();
while($mqtt->proc()){
		
}
echo "data: closed\n\n";
$mqtt->close();

?>
