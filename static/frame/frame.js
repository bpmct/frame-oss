$(document).foundation();

let controls = $(".controls-nav");

toggleMenu = () => {
  controls.is(":visible") ? controls.fadeOut(100) : controls.fadeIn(100);
};

toggleFullScreen = () => {
  var targetelement = document.documentElement;
  if (targetelement.requestFullscreen) {
    targetelement.requestFullscreen();
  }
  if (targetelement.webkitRequestFullscreen) {
    targetelement.webkitRequestFullscreen();
  }
  if (targetelement.mozRequestFullScreen) {
    targetelement.mozRequestFullScreen();
  }
  if (targetelement.msRequestFullscreen) {
    targetelement.msRequestFullscreen();
  }
};

// allow for taps or double taps
var cooldown = false;
$(".overlay").on("click", function (e) {
  if (!cooldown) {
    cooldown = true;
    toggleMenu();
    setTimeout(() => (cooldown = false), 200);
  }
});

// $(".fullscreen-image-slider").dblclick(toggleMenu);
