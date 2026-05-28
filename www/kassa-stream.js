(function(window) {
  function createSessionStream(options) {
    var source = null;
    var streamReconnectTimer = null;
    var streamReconnectDelay = 1000;

    function scheduleStreamReconnect() {
      if(streamReconnectTimer) return;
      if(source) {
        source.close();
        source = null;
      }
      streamReconnectTimer = setTimeout(function() {
        streamReconnectTimer = null;
        connectStream();
      }, streamReconnectDelay);
      streamReconnectDelay = Math.min(streamReconnectDelay * 2, 30000);
    }

    function connectStream() {
      source = new EventSource('stream.php?session='+encodeURIComponent(options.session)+'&t='+(new Date()).getTime());
      source.onopen = function() {
        streamReconnectDelay = 1000;
      };
      source.onmessage = function(event) {
        if(event.data === "closed") {
          scheduleStreamReconnect();
          return;
        }
        var data;
        try {
          data=JSON.parse(event.data);
        } catch(error) {
          if(options.onInvalidMessage) options.onInvalidMessage(event.data, error);
          return;
        }
        options.onMessage(data[0], data[1]);
      };
      source.onerror = function() {
        scheduleStreamReconnect();
      };
      return source;
    }

    connectStream();

    return {
      reconnect: scheduleStreamReconnect,
      source: function() {
        return source;
      },
    };
  }

  window.HackBankStream = {
    createSessionStream: createSessionStream,
  };
})(window);
