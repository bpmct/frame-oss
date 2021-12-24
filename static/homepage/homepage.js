let frameID = document.getElementById("frame_id");
let submitButton = document.getElementById("go_to_frame");

submitButton.onclick = function () {
  if (frameID.value == "") {
    alert("Please enter a frame ID");
  } else if (frameID.value == "demo") {
    window.location.href = "/fjsyDoKNNo";
  } else {
    window.location.href = "/" + frameID.value;
  }
};
