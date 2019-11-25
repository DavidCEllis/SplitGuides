// This is the code to listen to server events sent by flask.

const splits = document.getElementById("splits")
const eventsource = new EventSource("splits")

eventsource.onmessage = function(e) {
  splits.innerHTML = e.data
}
