$(document).foundation();

let controls = $(".controls-nav");
let menuButton = $(".menu-button");
let darkOverlay = $(".dark-overlay");

toggleMenu = () => {
  if (controls.is(":visible")) {
    // hide menu
    controls.fadeOut(100);

    // show menu button, if exists
    menuButton.length && menuButton.fadeIn(100);

    // hide dark overlay, if exists
    darkOverlay.length && darkOverlay.fadeOut(300);
  } else {
    // show menu
    controls.fadeIn(100);

    // hide menu button, if exists
    menuButton.length && menuButton.fadeOut(100);

    // show menu overlay, if exists
    darkOverlay.length && darkOverlay.fadeIn(300);
  }
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
