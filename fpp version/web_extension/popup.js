document.getElementById("start").addEventListener("click", function () {
  chrome.tabs.create({ url: "http://localhost:5000" });
});