// This is the code to listen to server events sent by flask.

const splits = document.getElementById("splits")
const evtSource = new EventSource("splits")

splits.innerHTML = "<strong>Loading...</strong>"

console.log(evtSource)

evtSource.onmessage = function(e) {
  if (e.data) {
    splits.innerHTML = e.data
  }
}

evtSource.onerror = function(err) {
  console.error("EventSource failed:", err)
}
