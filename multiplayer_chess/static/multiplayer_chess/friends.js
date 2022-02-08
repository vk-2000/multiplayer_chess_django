const chatSocket = new WebSocket(
  "ws://" + window.location.host + "/ws/multiplayer_chess/home"
);

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  friend_name = data["friend_name"];
  console.log(friend_name + " wants to play");
  let choice = confirm(friend_name + " wants to play with you");
  if (choice == true) {
    window.location.href = getFriendMatchUrl(friend_name);
  }
};

input = document.querySelector("#friendSearch");
btnFriendSearch = document.querySelector("#friendSearchButton");
diplayContainer = document.querySelector("#searchResult");
let friend_name;
btnFriendSearch.addEventListener("click", () => {
  friend_name = input.value;

  let url = getPlayerExistsUrl(friend_name);
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      if (!data["exists"]) {
        alert(data["msg"]);
      } else {
        displayPlayer(friend_name);
      }
    });
});

function displayPlayer(friend_name) {
  document.querySelector("#searchResultContainer").classList.remove("d-none");
  document.querySelector("#searchResultContainer").classList.add("d-flex");
  document.querySelector("#searchResultName").innerText = friend_name;
}
document.querySelector("#btnSendRequest").addEventListener("click", () => {
  let url = getSendRequestUrl(friend_name);
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      alert(data["msg"]);
    });
});
